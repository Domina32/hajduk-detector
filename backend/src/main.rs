#[macro_use]
extern crate rocket;

mod api;
mod database;

#[launch]
fn rocket() -> _ {
    rocket::build()
        .attach(api::fairings::CORS)
        .mount("/", routes![api::endpoints::schedule])
}
