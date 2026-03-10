variable "db_url" {
  type    = string
  default = getenv("DATABASE_URL")
}

env "supabase" {
  url = var.db_url
  migration {
    dir = "file://migrations"
  }
}

env "local" {
  src = "file://schema.sql"
  migration {
    dir = "file://migrations"
  }
  dev = "docker://postgres/15/dev"
}