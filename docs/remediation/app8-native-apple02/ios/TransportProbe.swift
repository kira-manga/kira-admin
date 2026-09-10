import UIKit
import Foundation
import CFNetwork
import Darwin

// UNEXECUTED private draft. Primary owns simulator/egress isolation and external deadline.
@main
final class TransportProbe: UIResponder, UIApplicationDelegate, URLSessionDataDelegate {
    var window: UIWindow?
    private let hosts = ["raijinscan.co", "app8-probe.raijinscan.co"]
    private var phase = "", nonce = ""
    private var port = 0, index = 0
    private var session: URLSession?
    private var observations: [[String: Any]] = []
    private var row: [String: Any] = [:]
    private var body = Data()
    private var status: Int?
    private var violation = ""
    private var metrics: [[String: Any]] = []
    private var finished = false

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        window = UIWindow(frame: UIScreen.main.bounds)
        window?.rootViewController = UIViewController()
        window?.makeKeyAndVisible()
        DispatchQueue.main.async { self.begin() }
        return true
    }

    private func begin() {
        let env = ProcessInfo.processInfo.environment
        phase = env["APP8_PHASE"] ?? ""
        nonce = env["APP8_NONCE"] ?? ""
        port = Int(env["APP8_PORT"] ?? "") ?? 0
        guard ["allow", "deny"].contains(phase),
              nonce.range(of: "^[0-9a-f]{32}$", options: .regularExpression) != nil,
              (1...65535).contains(port) else { finish(false, "Invalid phase/nonce/owned port"); return }
        let info = Bundle.main.infoDictionary ?? [:]
        let atsKeys = info.keys.filter { $0.hasPrefix("NSAppTransportSecurity") }
        let oldATS: [String: Any] = ["NSExceptionDomains": ["raijinscan.co": [
            "NSExceptionAllowsInsecureHTTPLoads": true, "NSIncludesSubdomains": true]]]
        let loaded = info["NSAppTransportSecurity"] as? NSDictionary
        let policyMatches = phase == "allow"
            ? atsKeys == ["NSAppTransportSecurity"] && loaded?.isEqual(to: oldATS) == true
            : atsKeys.isEmpty
        guard policyMatches, Bundle.main.bundleIdentifier == "me.manga.kira.transportprobe",
              info["MinimumOSVersion"] as? String == "15.0" else {
            finish(false, "Unexpected loaded policy/bundle/deployment metadata"); return
        }
        let config = URLSessionConfiguration.ephemeral
        config.urlCache = nil
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        config.httpCookieStorage = nil
        config.httpShouldSetCookies = false
        config.urlCredentialStorage = nil
        config.httpShouldUsePipelining = false
        config.httpMaximumConnectionsPerHost = 1
        config.timeoutIntervalForRequest = 3
        config.timeoutIntervalForResource = 6
        config.waitsForConnectivity = false
        config.allowsCellularAccess = false
        // A manual per-session HTTP proxy, never nil/system/PAC or a list containing DIRECT.
        // The fixture never forwards. Metrics detect (but cannot prevent) misrouting;
        // the primary must settle effective no-DNS/no-external isolation before launch.
        config.connectionProxyDictionary = [
            kCFNetworkProxiesHTTPEnable as String: 1,
            kCFNetworkProxiesHTTPProxy as String: "127.0.0.1",
            kCFNetworkProxiesHTTPPort as String: port,
            "ProxyAutoConfigEnable": 0, "ProxyAutoDiscoveryEnable": 0,
            "ExcludeSimpleHostnames": 0, "ExceptionsList": [String]()
        ]
        session = URLSession(configuration: config, delegate: self, delegateQueue: .main)
        next()
    }

    private func next() {
        guard index < hosts.count else { finish(true, ""); return }
        let url = URL(string: "http://\(hosts[index])/\(nonce)")!
        body = Data(); status = nil; violation = ""; metrics = []
        row = ["url": url.absoluteString]
        var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 3)
        request.httpShouldHandleCookies = false
        request.setValue("close", forHTTPHeaderField: "Connection")
        request.setValue("text/plain", forHTTPHeaderField: "Accept")
        request.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
        request.setValue("App8NativePolicyProbe/1", forHTTPHeaderField: "User-Agent")
        session!.dataTask(with: request).resume()
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse,
                    completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        guard let http = response as? HTTPURLResponse else {
            violation = "Non-HTTP response"; completionHandler(.cancel); return
        }
        status = http.statusCode
        row["responseURL"] = http.url?.absoluteString ?? ""
        if phase != "allow" || status != 200 || http.url?.absoluteString != row["url"] as? String
            || http.value(forHTTPHeaderField: "X-App8-Nonce") != nonce
            || http.value(forHTTPHeaderField: "X-App8-Host") != hosts[index]
            || http.expectedContentLength > 512 {
            violation = "Unexpected HTTP response"; completionHandler(.cancel); return
        }
        completionHandler(.allow)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        if body.count + data.count > 512 {
            violation = "Oversized fixture body"; dataTask.cancel(); return
        }
        body.append(data)
    }

    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) {
        violation = "Redirect rejected"; completionHandler(nil)
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didReceive challenge: URLAuthenticationChallenge,
                    completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        violation = "Authentication challenge rejected"; completionHandler(.cancelAuthenticationChallenge, nil)
    }

    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge,
                    completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        violation = "Session authentication challenge rejected"; completionHandler(.cancelAuthenticationChallenge, nil)
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didFinishCollecting collected: URLSessionTaskMetrics) {
        metrics = collected.transactionMetrics.map { metric in
            ["proxy": metric.isProxyConnection, "remoteAddress": metric.remoteAddress ?? "",
             "remotePort": metric.remotePort ?? -1,
             "networkLoad": metric.resourceFetchType == .networkLoad,
             "dnsStartRecorded": metric.domainLookupStartDate != nil,
             "dnsEndRecorded": metric.domainLookupEndDate != nil,
             "protocol": metric.networkProtocolName ?? ""] as [String: Any]
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        let failure = error as NSError?
        let expected = Data("app8-no-forward \(nonce) \(hosts[index])\n".utf8)
        if metrics.contains(where: {
            let address = $0["remoteAddress"] as? String ?? ""
            return !address.isEmpty && (!["127.0.0.1", "::ffff:127.0.0.1"].contains(address)
                || ($0["remotePort"] as? Int) != port)
        }) { violation = "Metrics show a non-fixture remote endpoint" }
        let proxyConfirmed = metrics.count == 1 && metrics.allSatisfy {
            ($0["proxy"] as? Bool) == true && ($0["networkLoad"] as? Bool) == true
                && ["127.0.0.1", "::ffff:127.0.0.1"].contains($0["remoteAddress"] as? String ?? "")
                && ($0["remotePort"] as? Int) == port
        }
        let allowed = phase == "allow" && failure == nil && status == 200 && body == expected && proxyConfirmed
        let denied = phase == "deny" && failure?.domain == NSURLErrorDomain
            && failure?.code == URLError.Code.appTransportSecurityRequiresSecureConnection.rawValue
            && status == nil && task.response == nil && body.isEmpty
        row["responseCode"] = status.map { $0 as Any } ?? NSNull()
        row["receivedBodyBytes"] = body.count
        row["metrics"] = metrics
        row["errorDomain"] = failure?.domain ?? ""
        row["errorCode"] = failure?.code ?? 0
        row["errorDescription"] = failure?.localizedDescription ?? ""
        row["violation"] = violation
        row["outcome"] = allowed ? "canned-response" : denied ? "native-ATS-policy-rejection" : "unexpected"
        observations.append(row)
        guard violation.isEmpty && (allowed || denied) else { finish(false, "Native observation failed"); return }
        index += 1
        next()
    }

    private func finish(_ ok: Bool, _ failure: String) {
        guard !finished else { return }
        finished = true
        session?.invalidateAndCancel()
        let result: [String: Any] = ["ok": ok && observations.count == 2, "failure": failure,
            "phase": phase, "nonce": nonce, "proxyHost": "127.0.0.1", "proxyPort": port,
            "systemVersion": UIDevice.current.systemVersion, "deploymentTarget": "15.0",
            "loadedATS": Bundle.main.infoDictionary?["NSAppTransportSecurity"] ?? NSNull(),
            "observations": observations, "minimumIOS15RuntimeProven": false]
        do {
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
            let output = URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Documents/app8-result.json")
            try data.write(to: output, options: [.atomic])
            print("APP8_NATIVE_RESULT " + String(decoding: data, as: UTF8.self)); fflush(stdout)
            exit(ok && observations.count == 2 ? 0 : 1)
        } catch {
            print("APP8_NATIVE_RESULT_WRITE_FAILED"); fflush(stdout); exit(1)
        }
    }
}
