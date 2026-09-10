package me.manga.kira.transportprobe;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.pm.ApplicationInfo;
import android.os.Build;
import android.os.Bundle;
import android.security.NetworkSecurityPolicy;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.Authenticator;
import java.net.CookieHandler;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.ProxySelector;
import java.net.ResponseCache;
import java.net.SocketAddress;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

/** UNEXECUTED private draft. Primary owns the device, egress isolation, and deadline. */
public final class TransportProbe extends Instrumentation {
    private static final String[] HOSTS = {"raijinscan.co", "app8-probe.raijinscan.co"};
    private Bundle arguments;

    @Override public void onCreate(Bundle supplied) {
        super.onCreate(supplied);
        arguments = supplied;
        start();
    }

    @Override public void onStart() {
        JSONObject result = new JSONObject();
        JSONArray observations = new JSONArray();
        boolean ok = false;
        try {
            String phase = arguments.getString("phase", "");
            String nonce = arguments.getString("nonce", "");
            int port = Integer.parseInt(arguments.getString("port", "0"));
            require(phase.equals("allow") || phase.equals("deny"), "Unknown phase");
            require(nonce.matches("[0-9a-f]{32}"), "Expected fresh 32-hex nonce");
            require(port > 0 && port <= 65535, "Invalid owned proxy port");
            ApplicationInfo app = getTargetContext().getApplicationInfo();
            result.put("phase", phase).put("nonce", nonce).put("proxyPort", port)
                .put("proxyHost", "127.0.0.1").put("sdk", Build.VERSION.SDK_INT)
                .put("minSdk", app.minSdkVersion).put("targetSdk", app.targetSdkVersion)
                .put("observations", observations);
            require(Build.VERSION.SDK_INT == 26, "This bounded probe requires API26");
            require(app.minSdkVersion == 26 && app.targetSdkVersion == 36, "Wrong SDK levels");
            require((app.flags & ApplicationInfo.FLAG_DEBUGGABLE) == 0, "Debuggable host");
            require(app.packageName.equals("me.manga.kira.transportprobe"), "Wrong host package");

            CookieHandler.setDefault(null);
            ResponseCache.setDefault(null);
            Authenticator.setDefault(null);
            HttpURLConnection.setFollowRedirects(false);
            // No PAC/system route or implicit Proxy.NO_PROXY path is allowed by this host.
            ProxySelector.setDefault(new ProxySelector() {
                @Override public List<Proxy> select(URI uri) {
                    throw new IllegalStateException("Unexpected default proxy selection");
                }
                @Override public void connectFailed(URI uri, SocketAddress address, IOException error) {
                    throw new IllegalStateException("Unexpected proxy fallback", error);
                }
            });
            InetAddress loopback = InetAddress.getByAddress(new byte[] {127, 0, 0, 1});
            Proxy proxy = new Proxy(Proxy.Type.HTTP, new InetSocketAddress(loopback, port));
            for (String host : HOSTS) {
                JSONObject row = new JSONObject();
                observations.put(row);
                observe(row, host, nonce, phase.equals("allow"), proxy);
            }
            ok = observations.length() == 2;
        } catch (Exception failure) {
            try { result.put("failure", failure.getClass().getName() + ": " + failure.getMessage()); }
            catch (Exception ignored) { /* Missing valid JSON/result is never accepted by the caller. */ }
        }
        Bundle output = new Bundle();
        try { result.put("ok", ok); }
        catch (Exception ignored) { ok = false; }
        output.putString("stream", "APP8_NATIVE_RESULT " + result.toString() + "\n");
        finish(ok ? Activity.RESULT_OK : Activity.RESULT_CANCELED, output);
    }

    private static void observe(JSONObject row, String host, String nonce, boolean allow, Proxy proxy)
            throws Exception {
        URL url = new URL("http://" + host + "/" + nonce);
        boolean permitted = NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted(host);
        row.put("url", url.toExternalForm()).put("policyPermits", permitted)
            .put("responseCode", JSONObject.NULL).put("receivedBodyBytes", 0);
        require(permitted == allow, "Loaded policy mismatch for " + host);
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) url.openConnection(proxy);
            connection.setConnectTimeout(3000);
            connection.setReadTimeout(3000);
            connection.setInstanceFollowRedirects(false);
            connection.setUseCaches(false);
            connection.setAllowUserInteraction(false);
            connection.setRequestProperty("Connection", "close");
            connection.setRequestProperty("Accept", "text/plain");
            connection.setRequestProperty("Accept-Encoding", "identity");
            connection.setRequestProperty("User-Agent", "App8NativePolicyProbe/1");
            int status = connection.getResponseCode();
            row.put("responseCode", status).put("usingProxy", connection.usingProxy());
            require(allow, "Candidate unexpectedly reached HTTP response");
            require(status == 200 && connection.usingProxy(), "Control did not use fixture proxy");
            require(connection.getURL().equals(url), "Unexpected response URL");
            require(nonce.equals(connection.getHeaderField("X-App8-Nonce")), "Wrong fixture nonce");
            require(host.equals(connection.getHeaderField("X-App8-Host")), "Wrong fixture host");
            byte[] expected = ("app8-no-forward " + nonce + " " + host + "\n")
                .getBytes(StandardCharsets.UTF_8);
            byte[] body;
            try (InputStream stream = connection.getInputStream()) { body = readBounded(stream); }
            row.put("receivedBodyBytes", body.length);
            require(Arrays.equals(body, expected), "Control did not receive exact canned body");
            row.put("outcome", "canned-response");
        } catch (IOException failure) {
            row.put("errorClass", failure.getClass().getName()).put("errorMessage", failure.getMessage());
            require(!allow && failure.getClass() == IOException.class
                && ("Cleartext HTTP traffic to " + host + " not permitted").equals(failure.getMessage())
                && row.isNull("responseCode"), "Not the API26 native cleartext-policy rejection");
            row.put("outcome", "native-cleartext-policy-rejection");
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static byte[] readBounded(InputStream stream) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[128];
        int count;
        while ((count = stream.read(buffer)) != -1) {
            if (output.size() + count > 512) throw new IOException("Oversized fixture body");
            output.write(buffer, 0, count);
        }
        return output.toByteArray();
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }
}
