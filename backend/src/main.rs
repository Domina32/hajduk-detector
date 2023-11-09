#[macro_use]
extern crate rocket;
use rocket::fairing::{Fairing, Info, Kind};
use rocket::http::Header;
use rocket::serde::{json, Deserialize, Serialize};
use rocket::{Request, Response};
use std::fs;

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

#[derive(Serialize, Deserialize, Debug)]
#[serde(crate = "rocket::serde")]
struct Game {
    teams: String,
    location: String,
    datetime: String,
}

#[get("/schedule")]
fn schedule() -> json::Json<Box<[Game]>> {
    let games_json: String =
        fs::read_to_string("/home/animod/Git/hajduk-detector/app/src/mocks/scraped.json").unwrap();
    let games: Box<[Game]> = json::from_str::<Box<[Game]>>(&games_json).unwrap();

    json::Json(games)
}

#[launch]
fn rocket() -> _ {
    rocket::build().attach(CORS).mount("/", routes![schedule])
}
