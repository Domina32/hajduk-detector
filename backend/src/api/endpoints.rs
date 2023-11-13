use crate::database;
use rocket::serde::json;
use std::fs;

#[get("/schedule")]
pub fn schedule() -> json::Json<Box<[database::models::Game]>> {
    let games_json: String =
        fs::read_to_string("/home/animod/Git/hajduk-detector/app/src/mocks/scraped.json").unwrap();
    let games: Box<[database::models::Game]> =
        json::from_str::<Box<[database::models::Game]>>(&games_json).unwrap();

    json::Json(games)
}
