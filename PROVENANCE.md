## Verifying SDK build provenance with the SLSA framework

LaunchDarkly uses the [SLSA framework](https://slsa.dev/spec/v1.0/about) (Supply-chain Levels for Software Artifacts) to help developers make their supply chain more secure by ensuring the authenticity and build integrity of our published SDK packages.

As part of [SLSA requirements for level 3 compliance](https://slsa.dev/spec/v1.0/requirements), LaunchDarkly publishes provenance about our SDK package builds using [GitHub's generic SLSA3 provenance generator](https://github.com/slsa-framework/slsa-github-generator/blob/main/internal/builders/generic/README.md#generation-of-slsa3-provenance-for-arbitrary-projects) for distribution alongside our packages. These attestations are available for download from the GitHub release page for the release version under Assets > `multiple.intoto.jsonl`.

To verify SLSA provenance attestations, we recommend using [slsa-verifier](https://github.com/slsa-framework/slsa-verifier). Example usage for verifying a package is included below:

<!-- x-release-please-start-version -->
```
# Set the version of the library to verify
VERSION=1.1.0
```
<!-- x-release-please-end -->


```
# Download package from PyPi
$ pip download --only-binary=:all: launchdarkly-server-sdk-otel==${VERSION}

# Download provenance from Github release into same directory
$ curl --location -O \
  https://github.com/launchdarkly/python-server-sdk-otel/releases/download/${VERSION}/multiple.intoto.jsonl

# Run slsa-verifier to verify provenance against package artifacts 
$ slsa-verifier verify-artifact \
--provenance-path multiple.intoto.jsonl \
--source-uri github.com/launchdarkly/python-server-sdk-otel \
launchdarkly_server_sdk_otel-${VERSION}-py3-none-any.whl
```

Below is a sample of expected output.

```
Verified signature against tlog entry index 89939519 at URL: https://rekor.sigstore.dev/api/v1/log/entries/24296fb24b8ad77abb8d2f681b007c76a4fe9f89cd9574918683ac8bc87cd6834c5baa479ae5cb98
Verified build using builder "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v1.10.0" at commit 984fc268df29918b03f51f2507146f66d8668d03
Verifying artifact launchdarkly_server_sdk_otel-1.0.0-py3-none-any.whl: PASSED

PASSED: Verified SLSA provenance
```

Alternatively, to verify the provenance manually, the SLSA framework specifies [recommendations for verifying build artifacts](https://slsa.dev/spec/v1.0/verifying-artifacts) in their documentation.

**Note:** These instructions do not apply when building our libraries from source. 
