use rocket::fairing::{Fairing, Info, Kind};
use rocket::http::Header;
use rocket::{Build, Request, Response, Rocket};
use rocket_sync_db_pools::database;

pub struct CORS;

#[rocket::async_trait]
impl Fairing for CORS {
    fn info(&self) -> Info {
        Info {
            name: "Add CORS headers to responses",
            kind: Kind::Response,
        }
    }

    async fn on_response<'r>(&self, _request: &'r Request<'_>, response: &mut Response<'r>) {
        response.set_header(Header::new("Access-Control-Allow-Origin", "*"));
        response.set_header(Header::new(
            "Access-Control-Allow-Methods",
            "POST, GET, PATCH, OPTIONS",
        ));
        response.set_header(Header::new("Access-Control-Allow-Headers", "*"));
        response.set_header(Header::new("Access-Control-Allow-Credentials", "true"));
    }
}

#[database("diesel")]
pub struct Db(diesel::SqliteConnection);

#[rocket::async_trait]
impl Fairing for Db {
    fn info(&self) -> Info {
        Info {
            name: "Run pending migrations",
            kind: Kind::Ignite,
        }
    }

    async fn on_ignite(&self, rocket: Rocket<Build>) -> Result<Rocket<Build>, Rocket<Build>> {
        use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};

        const MIGRATIONS: EmbeddedMigrations = embed_migrations!("migrations");

        Db::get_one(&rocket)
            .await
            .expect("database connection")
            .run(|conn| {
                conn.run_pending_migrations(MIGRATIONS)
                    .expect("diesel migrations");
            })
            .await;

        Ok(rocket)
    }
}
