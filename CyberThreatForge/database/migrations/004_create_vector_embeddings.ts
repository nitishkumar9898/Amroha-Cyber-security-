import type { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('vector_embeddings', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.string('resource_type').notNullable(); // evidence, case, ioc, entity
    t.uuid('resource_id').notNullable();
    t.string('model').notNullable();
    t.specificType('embedding', 'vector(1536)').notNullable();
    t.jsonb('metadata').defaultTo('{}');
    t.timestamps(true, true);

    t.index('resource_type');
    t.index(['resource_type', 'resource_id']);
  });

  // Create IVFFlat index for approximate nearest neighbor search
  await knex.raw(`
    CREATE INDEX idx_embedding_cosine ON vector_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
  `);
}

export async function down(knex: Knex): Promise<void> {
  await knex.raw('DROP INDEX IF EXISTS idx_embedding_cosine');
  await knex.schema.dropTableIfExists('vector_embeddings');
}
