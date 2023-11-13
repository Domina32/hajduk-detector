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
