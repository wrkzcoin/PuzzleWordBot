SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';
SET NAMES utf8mb4;

DROP TABLE IF EXISTS `puzzleBot_asked`;
CREATE TABLE `puzzleBot_asked` (
  `id` bigint(16) NOT NULL AUTO_INCREMENT,
  `question` varchar(2048) NOT NULL,
  `correct_answer` varchar(1024) NOT NULL,
  `winner_name` varchar(1024) DEFAULT NULL,
  `winner_id` varchar(32) DEFAULT NULL,
  `score_value` smallint(4) DEFAULT NULL,
  `inserted_date` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `puzzleBot_score`;
CREATE TABLE `puzzleBot_score` (
  `sid` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(32) NOT NULL,
  `name` varchar(64) CHARACTER SET utf8mb4 DEFAULT NULL,
  `total_win` int(11) DEFAULT NULL,
  `score` bigint(16) DEFAULT NULL,
  `last_scored` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`sid`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
