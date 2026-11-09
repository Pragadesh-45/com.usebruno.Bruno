## Publishing

How to ship a new Bruno version to Flathub. Replace `X.Y.Z` with the version throughout.

### 1. Branch

```bash
git fetch upstream
git switch -c release/vX.Y.Z upstream/master
```

### 2. Get the AppImage details

Wait until the AppImage is attached to the upstream release, then download it:

```bash
curl -LO https://github.com/usebruno/bruno/releases/download/vX.Y.Z/bruno_X.Y.Z_x86_64_linux.AppImage

# Get the checksum of AppImage
shasum -a 256 bruno_X.Y.Z_x86_64_linux.AppImage

# Get the size of AppImage (macOS; use `stat -c%s` on Linux)
stat -f%z bruno_X.Y.Z_x86_64_linux.AppImage
```

### 3. Update the manifest

In the `extra-data` source of the `bruno` module in `com.usebruno.Bruno.yml`, update `url`, `sha256` and `size`.

### 4. Update the metainfo and changelog

Add the release at the top of `<releases>` in `com.usebruno.Bruno.metainfo.xml`, using the upstream release date:

```xml
<release version="vX.Y.Z" date="YYYY-MM-DD"></release>
```

Then pull its notes from the upstream GitHub release. Release notes shown on Flathub come from the newest `<release>` entry; the script fills it and collapses older entries back to one line:

```bash
GITHUB_TOKEN=$(gh auth token) ./update-changelog.py
```

### 5. Lint

```bash
docker run --rm -v "$PWD":/w -w /w ghcr.io/flathub/flatpak-builder-lint:latest manifest com.usebruno.Bruno.yml
docker run --rm -v "$PWD":/w -w /w ghcr.io/flathub/flatpak-builder-lint:latest appstream com.usebruno.Bruno.metainfo.xml
```

### 6. Test the build (Linux)

```bash
flatpak run org.flatpak.Builder --force-clean --user --install --install-deps-from=flathub build com.usebruno.Bruno.yml
flatpak run com.usebruno.Bruno
```

Check that the app starts and shows the new version.

### 7. Open the PR

Commit as ``release: `vX.Y.Z` `` and open a PR against `master` on `flathub/com.usebruno.Bruno`. The Flathub bot builds it and posts a test build link; install that and check it before merging. After merge, Flathub publishes the update within a few hours.

### Bundled dependencies

Modules with `x-checker-data` in the manifest (such as `git`) are updated by the Flathub external data checker, which opens PRs on its own. No action is needed at release time; when merging one of those PRs, check that the new URL and sha256 match the upstream release.
