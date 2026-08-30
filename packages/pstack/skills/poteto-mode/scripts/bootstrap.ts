// PATCH-HERMES-NO-IMPLICIT-INSTALL
import { existsSync } from "node:fs";
import { join } from "node:path";

const scriptsDirectory = import.meta.dir;
const commanderPackagePath = join(
  scriptsDirectory,
  "node_modules",
  "commander",
  "package.json"
);

export function ensureDependenciesInstalled(): void {
  if (existsSync(commanderPackagePath)) return;
  throw new Error(
    "Poteto Mode dependencies are not provisioned. Do not install automatically; ask the operator to authorize `bun install --frozen-lockfile` in this scripts directory, then rerun."
  );
}
