# Stabilizing Render Node Builds

The `realestate-broker-ui` service experienced intermittent `npm` network
timeouts during Render builds. Render treats every build as a fresh install, so
there is no shared package cache between runs and transient network hiccups can
cause `npm install` to fail with `ECONNRESET`.

To mitigate this we now:

1. Provide an `.npmrc` inside `realestate-broker-ui/` that increases retry and
   timeout budgets while disabling the optional audit/fund requests that add
   extra network calls.
2. Set the same values at deploy time via `render.yaml` so that Render's build
   environment inherits them without any manual configuration in the dashboard.
3. Force IPv4 DNS resolution order through `NODE_OPTIONS` to avoid occasional
   IPv6 connectivity issues observed on some shared runners.

With these adjustments `npm install` retries longer before giving up, making the
build command more resilient to transient network failures on Render.
