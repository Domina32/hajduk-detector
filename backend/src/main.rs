#[macro_use]
extern crate rocket;

#[get("/schedule")]
fn schedule() -> &'static str {
    "Hello, schedule!"
}

#[launch]
fn rocket() -> _ {
    rocket::build().mount("/", routes![schedule])
}
