CREATE TABLE `Players` (
  `idPlayer` int NOT NULL AUTO_INCREMENT,
  `playguid` varchar(20),
  `name` varchar(100),
  PRIMARY KEY (`idPlayer`)
);

CREATE TABLE `Comps` (
  `idComp` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100),
  `year` date,
  PRIMARY KEY (`idComp`)
);

CREATE TABLE `Matches` (
  `idMatch` int NOT NULL AUTO_INCREMENT,
  `idComp` int,
  `date` date,
  `home` varchar(100),
  `away` varchar(100),
  `FT_Score` varchar(100),
  `HT_Score` varchar(100),
  PRIMARY KEY (`idMatch`),
  FOREIGN KEY (`idComp`) REFERENCES `Comps`(`idComp`)
);

CREATE TABLE `Player_Matches` (
  `idPlayer` int,
  `idMatch` int,
  `position_num` int,
  `mins_played` int,
  `tries` Decimal(6,4),
  `try_assists` Decimal(6,4),
  `conversions` Decimal(6,4),
  `penalty_goals` Decimal(6,4),
  `drop_goals` Decimal(6,4),
  `meters_made` Decimal(6,4),
  `carries` Decimal(6,4),
  `possession_kicked_%` Decimal(6,4),
  `meters_kicked` Decimal(6,4),
  `balls_played_by_hand` Decimal(6,4),
  `passes_made` Decimal(6,4),
  `offloads` Decimal(6,4),
  `broken_tackles` Decimal(6,4),
  `knock_ons` Decimal(6,4),
  `tackles_made` Decimal(6,4),
  `missed_tackles` Decimal(6,4),
  `tackle_success_%` Decimal(6,4),
  `dominant_tackles_%` Decimal(6,4),
  `turnovers_won` Decimal(6,4),
  `turnovers_conceded` Decimal(6,4),
  `handling_errors` Decimal(6,4),
  `pens_conceded` Decimal(6,4),
  `offside_penalties` Decimal(6,4),
  `scrum_penalties` Decimal(6,4),
  `lineouts_won` Decimal(6,4),
  `lineouts_stolen` Decimal(6,4),
  `defemders_beaten` Decimal(6,4),
  `clean_breaks` Decimal(6,4),
  `at_home` int,
  `is_sub` int,
  FOREIGN KEY (`idMatch`) REFERENCES `Matches`(`idMatch`),
  FOREIGN KEY (`idPlayer`) REFERENCES `Players`(`idPlayer`)
);

