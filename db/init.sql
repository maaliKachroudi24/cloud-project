-- ════════════════════════════════════════════════════════════════
-- init.sql – Initialisation PostgreSQL (Partie 2)
-- ════════════════════════════════════════════════════════════════

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Les tables sont créées par SQLAlchemy au démarrage des apps.
-- Ce script ajoute des index de performance et des données initiales.

-- Commentaire de la base
COMMENT ON DATABASE grh IS 'Base de données GRH - ISAMM 2ING Mini-Projet Cloud 2026';
