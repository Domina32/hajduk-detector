use crate::database::schema::games;
use diesel::prelude::*;
use rocket::serde::{Deserialize, Serialize};

#[derive(Queryable, Selectable)]
#[diesel(table_name = crate::database::schema::games)]
#[diesel(check_for_backend(diesel::sqlite::Sqlite))]
#[derive(Serialize, Deserialize, Debug)]
#[serde(crate = "rocket::serde")]
pub struct Game {
    pub id: i32,
    pub teams: String,
    pub location: String,
    pub datetime: String,
}

#[derive(Insertable)]
#[diesel(table_name = games)]
pub struct NewGame<'a> {
    pub teams: &'a str,
    pub location: &'a str,
    pub datetime: &'a str,
}
