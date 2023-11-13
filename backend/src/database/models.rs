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
