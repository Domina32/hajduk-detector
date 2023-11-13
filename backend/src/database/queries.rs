use diesel::{QueryDsl, SelectableHelper, SqliteConnection};

use crate::database::{
    establish_connection,
    models::{Game, NewGame},
};

pub fn get_games() -> Vec<Game> {
    use crate::database::schema::games::dsl::*;
    let connection = &mut establish_connection();
    let results = diesel::RunQueryDsl::load(
        games
            .limit(5)
            .select(crate::database::models::Game::as_select()),
        connection,
    )
    .expect("Error loading games");

    results

    // println!("Displaying {} games", results.len());
    // for game in results {
    //     println!("{}", game.teams);
    //     println!("-----------\n");
    //     println!("{}", game.location);
    //     println!("-----------\n");
    //     println!("{}", game.datetime);
    // }
}

pub fn create_game(
    conn: &mut SqliteConnection,
    teams: &str,
    location: &str,
    datetime: &str,
) -> Game {
    use crate::database::schema::games;

    let new_game = NewGame {
        teams,
        location,
        datetime,
    };

    diesel::RunQueryDsl::get_result(
        diesel::insert_into(games::table)
            .values(&new_game)
            .returning(Game::as_returning()),
        conn,
    )
    .expect("Error saving new game")
}
