import neo4j, { Driver, Session } from 'neo4j-driver'
import type { AuthToken } from 'neo4j-driver'

const uri = process.env.NEXT_PUBLIC_NEO4J_URI || 'bolt://localhost:7687'
const user = process.env.NEO4J_USERNAME || 'neo4j'
const password = process.env.NEO4J_PASSWORD || ''

const authToken: AuthToken = neo4j.auth.basic(user, password)

export const driver: Driver = neo4j.driver(uri, authToken)

export const getSession = (): Session => driver.session()

// Close driver on app shutdown (use in a cleanup hook if needed)
export const closeDriver = (): void => {
  driver.close()
}