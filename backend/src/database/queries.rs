use crate::database::models::{Game, NewGame};

fn get_games() {
    use database::schema::games::dsl::*;

    let connection = &mut establish_connection();
    let results = games
        .limit(5)
        .select(database::models::Game::as_select())
        .load(connection)
        .expect("Error loading games");

    println!("Displaying {} games", results.len());
    for game in results {
        println!("{}", game.teams);
        println!("-----------\n");
        println!("{}", game.location);
        println!("-----------\n");
        println!("{}", game.datetime);
    }
}

fn create_game(conn: &mut SqliteConnection, teams: &str, location: &str, datetime: &str) -> Game {
    use crate::database::schema::games;

    let new_game = NewGame {
        teams,
        location,
        datetime,
    };

    diesel::insert_into(games::table)
        .values(&new_game)
        .returning(Game::as_returning())
        .get_result(conn)
        .expect("Error saving new game")
}
