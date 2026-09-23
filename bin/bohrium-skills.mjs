#!/usr/bin/env node

import { cp, mkdir, readFile, readdir, rename, rm, stat, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PACKAGE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST_PATH = path.join(PACKAGE_ROOT, "skill-manifest.json");
const SKILLS_ROOT = path.join(PACKAGE_ROOT, "skills");

const fail = (message) => {
  console.error(`bohrium-skills: ${message}`);
  process.exitCode = 1;
};

async function loadManifest() {
  return JSON.parse(await readFile(MANIFEST_PATH, "utf8"));
}

async function isDirectory(candidate) {
  try {
    return (await stat(candidate)).isDirectory();
  } catch {
    return false;
  }
}

function parseOptions(argv) {
  const [command = "help", ...rest] = argv;
  const options = { command, skills: [], force: false, dryRun: false };
  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (token === "--force") options.force = true;
    else if (token === "--dry-run") options.dryRun = true;
    else if (token === "--all") options.all = true;
    else if (token === "--scope") options.scope = rest[++index];
    else if (token === "--target") options.target = rest[++index];
    else if (token === "--skills") options.skills = rest[++index]?.split(",").map((item) => item.trim()).filter(Boolean) ?? [];
    else if (token === "--help" || token === "-h") options.help = true;
    else throw new Error(`unknown option: ${token}`);
  }
  return options;
}

function usage() {
  console.log(`Usage:
  bohrium-skills list
  bohrium-skills doctor
  bohrium-skills install --scope user|project [--skills name1,name2] [--all] [--force] [--dry-run]
  bohrium-skills update --scope user|project [--skills name1,name2] [--force]

Scope targets:
  user     $CODEX_HOME/skills, or ~/.codex/skills when CODEX_HOME is unset
  project  ./.codex/skills in the current working directory
`);
}

async function resolveTarget(options) {
  if (options.target) return path.resolve(options.target);
  if (options.scope === "user") {
    const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
    return path.join(codexHome, "skills");
  }
  if (options.scope === "project") return path.join(process.cwd(), ".codex", "skills");
  throw new Error("install requires --scope user|project (or an explicit --target)");
}

async function selectedSkills(manifest, options) {
  const known = new Map(manifest.skills.map((entry) => [entry.name, entry]));
  let names;
  if (options.skills.length > 0) names = options.skills;
  else if (options.all) names = manifest.skills.map((entry) => entry.name);
  else names = manifest.skills.filter((entry) => entry.channel === manifest.defaultChannel).map((entry) => entry.name);

  const unknown = names.filter((name) => !known.has(name));
  if (unknown.length > 0) throw new Error(`unknown skill(s): ${unknown.join(", ")}`);
  for (const name of names) {
    const skillRoot = path.join(SKILLS_ROOT, name);
    if (!(await isDirectory(skillRoot)) || !(await isDirectory(path.join(skillRoot, "agents")))) {
      throw new Error(`package is missing the skill directory or agents metadata: ${name}`);
    }
    try {
      await stat(path.join(skillRoot, "SKILL.md"));
    } catch {
      throw new Error(`package is missing SKILL.md: ${name}`);
    }
  }
  return names;
}

async function listSkills(manifest) {
  for (const entry of manifest.skills) {
    console.log(`${entry.name}\t${entry.channel}\t${entry.description}`);
  }
}

async function doctor(manifest) {
  let errors = 0;
  for (const entry of manifest.skills) {
    const root = path.join(SKILLS_ROOT, entry.name);
    for (const required of ["SKILL.md", "agents/openai.yaml"]) {
      try {
        await stat(path.join(root, required));
      } catch {
        console.error(`FAIL ${entry.name}: missing ${required}`);
        errors += 1;
      }
    }
    if (entry.name !== path.basename(root)) {
      console.error(`FAIL ${entry.name}: directory name mismatch`);
      errors += 1;
    }
  }
  if (errors > 0) throw new Error(`${errors} package integrity check(s) failed`);
  console.log(`OK ${manifest.skills.length} skill package(s) passed integrity checks`);
}

async function install(manifest, options) {
  const names = await selectedSkills(manifest, options);
  const target = await resolveTarget(options);
  console.log(`${options.dryRun ? "Would install" : "Installing"} ${names.length} skill(s) into ${target}`);
  if (options.dryRun) {
    for (const name of names) console.log(`  ${name}`);
    return;
  }
  await mkdir(target, { recursive: true });
  for (const name of names) {
    const source = path.join(SKILLS_ROOT, name);
    const destination = path.join(target, name);
    if (await isDirectory(destination)) {
      if (!options.force) throw new Error(`${destination} already exists; use --force to replace it`);
      const backup = `${destination}.backup-${Date.now()}`;
      await rename(destination, backup);
      console.log(`  backed up ${name} -> ${path.basename(backup)}`);
    }
    const staging = `${destination}.staging-${process.pid}`;
    await rm(staging, { recursive: true, force: true });
    await cp(source, staging, { recursive: true, errorOnExist: true });
    await rename(staging, destination);
    console.log(`  installed ${name}`);
  }
  const record = {
    package: manifest.repository,
    version: (JSON.parse(await readFile(path.join(PACKAGE_ROOT, "package.json")))).version,
    installedAt: new Date().toISOString(),
    skills: names
  };
  await writeFile(path.join(target, ".bohrium-app-skills.json"), `${JSON.stringify(record, null, 2)}\n`, "utf8");
}

async function main() {
  try {
    const options = parseOptions(process.argv.slice(2));
    if (options.help || options.command === "help") return usage();
    const manifest = await loadManifest();
    if (options.command === "list") return await listSkills(manifest);
    if (options.command === "doctor") return await doctor(manifest);
    if (options.command === "install" || options.command === "update") return await install(manifest, options);
    throw new Error(`unknown command: ${options.command}`);
  } catch (error) {
    fail(error.message);
  }
}

await main();
