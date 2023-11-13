// @generated automatically by Diesel CLI.

diesel::table! {
    games (id) {
        id -> Integer,
        teams -> Text,
        location -> Text,
        datetime -> Text,
    }
}
