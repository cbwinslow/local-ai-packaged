import neo4j from 'neo4j-driver'

const NEO4J_URI = process.env.NEO4J_URI!

const driver = neo4j.driver(
  NEO4J_URI,
  neo4j.auth.basic(process.env.NEO4J_USER || 'neo4j', process.env.NEO4J_PASSWORD || 'password')
)

export default driver