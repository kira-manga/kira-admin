# frozen_string_literal: true

# Called only by the primary-admitted Darwin recipe; no test/framework/signing doubles.
require "rubygems"
require "digest"
require "json"
require "rbconfig"
raise "Real Apple runtime required" unless RUBY_PLATFORM.include?("darwin")

mode, source, tools, admission_path, admission_sha, *paths = ARGV
raise "Expected a source or artifacts proof" unless
  (mode == "source" && paths.length == 1) || (mode == "artifacts" && paths.length == 3)
raise "Canonical private tools/receipt paths required" unless
  File.realpath(tools) == tools && File.directory?(tools) &&
  File.realpath(admission_path) == admission_path && File.file?(admission_path) && File.size(admission_path) <= 262_144
admission_bytes = File.binread(admission_path)
raise "Installed REXML receipt binding differs" unless Digest::SHA256.hexdigest(admission_bytes) == admission_sha
admission = JSON.parse(admission_bytes)
gem_root = File.join(tools, "gems/gems/rexml-3.4.4")
gem_spec = File.join(tools, "gems/specifications/rexml-3.4.4.gemspec")
package_sha = "19e0a2c3425dfbf2d4fc1189747bdb2f849b6c5e74180401b15734bc97b5d142"
raise "Unadmitted REXML install or environment" unless
  admission.fetch("schema") == "app65-rexml-package-install-v1" && admission.fetch("toolsRoot") == tools &&
  admission.fetch("rexmlRoot") == gem_root && File.realpath(gem_root) == gem_root &&
  admission.fetch("package").values_at("name", "version", "bytes", "sha256") == ["rexml", "3.4.4", 105_984, package_sha] &&
  ENV.fetch("GEM_HOME") == File.join(tools, "gems") && ENV.fetch("GEM_PATH") == File.join(tools, "gems") &&
  File.realpath(gem_spec) == gem_spec && File.file?(gem_spec) && File.size(gem_spec) <= 1_048_576 &&
  Digest::SHA256.file(gem_spec).hexdigest == admission.fetch("gemspecSha256")
package_files = admission.fetch("packageFiles")
raise "Unbounded/incomplete package inventory" unless
  package_files.is_a?(Hash) && package_files.length.between?(1, 512) && package_files.key?("lib/rexml/document.rb")
file_digest = lambda do |relative|
  raise "Unsafe package-relative filename" unless relative.is_a?(String) &&
    !relative.start_with?("/") && !relative.include?("\\") && !relative.include?("\0") &&
    relative.split("/", -1).none? { |part| ["", ".", ".."].include?(part) }
  path = File.join(gem_root, relative)
  row = package_files.fetch(relative)
  raise "Unadmitted installed REXML file" unless File.realpath(path) == path && File.file?(path) &&
    row.fetch("bytes").between?(0, 1_048_576) && File.size(path) == row.fetch("bytes")
  actual = Digest::SHA256.file(path).hexdigest
  raise "REXML file differs from verified gem payload" unless actual == row.fetch("sha256")
  actual
end
package_files.each_key { |relative| file_digest.call(relative) }
rexml_feature = ->(path) { path.match?(%r{(?:\A|/)rexml(?:/|\.rb\z)}) }
raise "Unexpected preloaded REXML" if $LOADED_FEATURES.any? { |path| rexml_feature.call(path) }
gem "rexml", "= 3.4.4"
spec = Gem.loaded_specs.fetch("rexml")
raise "Locked canonical reader dependency required" unless spec.version.to_s == "3.4.4" &&
  spec.full_gem_path == gem_root && File.realpath(spec.full_gem_path) == gem_root &&
  spec.loaded_from == gem_spec && File.realpath(spec.loaded_from) == gem_spec
require File.join(source, "release/ios/lib/libwebp_notices")
notices = KiraRelease::LibwebpNotices
reader = KiraRelease::PlistReader

receipt = {"accepted" => false, "isolatedResourceProofOnly" => true}
if mode == "source"
  notices.validate_repository!(source)
  receipt["repositoryNoticeValidation"] = true
else
  built, binary, = paths
  source_bundle = File.join(source, "iosApp/iosApp/Settings.bundle")
  source_values = notices::RESOURCE_PATHS.to_h { |relative| [relative, reader.read(File.join(source_bundle, relative))] }
  receipt["bundles"] = {"built_app_as_packaged" => built, "apple_binary_roundtrip_copy" => binary}.to_h do |label, app|
    notices.validate_app!(app, repository_root: source)
    resources = notices::RESOURCE_PATHS.to_h do |relative|
      path = File.join(app, "Settings.bundle", relative)
      bytes = File.binread(path)
      is_binary = bytes.start_with?("bplist00")
      raise "Binary case did not execute" if label == "apple_binary_roundtrip_copy" && !is_binary
      value = reader.read(path) # Binary path invokes the real /usr/bin/plutil, never a stub.
      raise "Source/packaged plist values differ" unless value == source_values.fetch(relative)
      [relative, {"sha256" => Digest::SHA256.hexdigest(bytes), "bytes" => bytes.bytesize,
                  "encoding" => is_binary ? "binary1" : "xml", "decoded" => value}]
    end
    [label, {"app" => app, "productionNoticeValidatorPassed" => true, "resources" => resources}]
  end
end
# Capture only after every repository/app/resource read, including the actual Apple binary path.
raise "Selected REXML changed during proof" unless Gem.loaded_specs.fetch("rexml").equal?(spec) &&
  File.realpath(spec.full_gem_path) == gem_root && REXML::VERSION == "3.4.4" &&
  File.realpath(gem_spec) == gem_spec && Digest::SHA256.file(gem_spec).hexdigest == admission.fetch("gemspecSha256")
loaded = $LOADED_FEATURES.select { |path| path.start_with?(gem_root + "/") || rexml_feature.call(path) }.sort
raise "Incomplete/duplicate end-of-proof REXML inventory" unless loaded.length.between?(1, 512) &&
  loaded.uniq == loaded && loaded.include?(File.join(gem_root, "lib/rexml/document.rb"))
loaded_hashes = loaded.to_h do |path|
  raise "REXML loaded outside admitted canonical root" unless path.start_with?(gem_root + "/") && File.realpath(path) == path
  relative = path.delete_prefix(gem_root + "/")
  [relative, file_digest.call(relative)]
end
receipt["runtime"] = {"ruby" => RUBY_DESCRIPTION, "rubyExecutable" => RbConfig.ruby,
                      "rexmlVersion" => spec.version.to_s, "rexmlRoot" => gem_root,
                      "rexmlPackageSha256" => package_sha, "rexmlInstalledReceiptSha256" => admission_sha,
                      "gemspecSha256" => admission.fetch("gemspecSha256"),
                      "loadedRexmlAfterProof" => true, "loadedRexmlSha256" => loaded_hashes}
receipt["accepted"] = true # This proof only, not primary/run/shipping acceptance.
output = paths.last
File.open(output, File::WRONLY | File::CREAT | File::EXCL, 0o600) do |file|
  file.write(JSON.pretty_generate(receipt) + "\n")
end
puts "APP65_NOTICE_PROOF #{mode}: complete; not a shipping/signing/release result"
