import path from "node:path"
import { fileURLToPath } from "node:url"
import dotenv from "dotenv"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const rootDir = path.join(__dirname, "../..")

// Tracked dev defaults first, then the gitignored real secrets, which win.
dotenv.config({ path: path.join(rootDir, ".env") })
dotenv.config({ path: path.join(rootDir, ".env.local"), override: true })

function getEnvVar(name: string): string {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Environment variable ${name} is undefined`)
  }
  return value
}

export const firstSuperuser = getEnvVar("FIRST_SUPERUSER")
export const firstSuperuserPassword = getEnvVar("FIRST_SUPERUSER_PASSWORD")
