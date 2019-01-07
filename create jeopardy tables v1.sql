-- MySQL Script generated by MySQL Workbench
-- Mon Jan 22 11:19:45 2018
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema jeopardy
-- -----------------------------------------------------
-- Thomas' PY4E capstone project

-- -----------------------------------------------------
-- Schema jeopardy
--
-- Thomas' PY4E capstone project
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `jeopardy` DEFAULT CHARACTER SET utf8 ;
USE `jeopardy` ;

-- -----------------------------------------------------
-- Table `jeopardy`.`player`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`player` (
  `id` INT NOT NULL,
  `name` TEXT NOT NULL,
  `occupation` TEXT NULL,
  `hometown` TEXT NULL,
  `username` TEXT NULL,
  `notes` LONGTEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `player_id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`player_alias`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`player_alias` (
  `player_id` INT NOT NULL,
  `alias_id` INT NOT NULL,
  PRIMARY KEY (`player_id`, `alias_id`),
  INDEX `player_id_idx` (`alias_id` ASC),
  CONSTRAINT `player_id`
    FOREIGN KEY (`alias_id`)
    REFERENCES `jeopardy`.`player` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`season`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`season` (
  `id` INT NOT NULL,
  `name` TEXT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`game_type`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`game_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` TEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`game`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`game` (
  `id` INT NOT NULL,
  `show` INT NULL,
  `date` DATE NULL,
  `season_id` INT NOT NULL,
  `type_id` INT NOT NULL,
  `player1` INT NULL,
  `player2` INT NULL,
  `player3` INT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `id_idx` (`type_id` ASC),
  INDEX `player1_idx` (`player1` ASC),
  INDEX `player2_idx` (`player2` ASC),
  INDEX `player3_idx` (`player3` ASC),
  INDEX `season_id_idx` (`season_id` ASC),
  CONSTRAINT `game_type_id`
    FOREIGN KEY (`type_id`)
    REFERENCES `jeopardy`.`game_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `player1`
    FOREIGN KEY (`player1`)
    REFERENCES `jeopardy`.`player` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `player2`
    FOREIGN KEY (`player2`)
    REFERENCES `jeopardy`.`player` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `player3`
    FOREIGN KEY (`player3`)
    REFERENCES `jeopardy`.`player` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `season_id`
    FOREIGN KEY (`season_id`)
    REFERENCES `jeopardy`.`season` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '	';


-- -----------------------------------------------------
-- Table `jeopardy`.`category`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`category` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`round`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`round` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`clue_value`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`clue_value` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `amount` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`clue_type`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`clue_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`clue`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`clue` (
  `id` INT NOT NULL,
  `value_id` INT NULL,
  `round_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `type_id` INT NOT NULL,
  `text` TEXT NOT NULL,
  `answer` TEXT NOT NULL,
  `pos_x` INT NULL,
  `daily_double` TINYINT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`id`),
  INDEX `category_idx` (`category_id` ASC),
  INDEX `round_idx` (`round_id` ASC),
  INDEX `clue_value_idx` (`value_id` ASC),
  INDEX `clue_type_idx` (`type_id` ASC),
  CONSTRAINT `category`
    FOREIGN KEY (`category_id`)
    REFERENCES `jeopardy`.`category` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `round`
    FOREIGN KEY (`round_id`)
    REFERENCES `jeopardy`.`round` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `clue_value`
    FOREIGN KEY (`value_id`)
    REFERENCES `jeopardy`.`clue_value` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `clue_type`
    FOREIGN KEY (`type_id`)
    REFERENCES `jeopardy`.`clue_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`place`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`place` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `tied` TINYINT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`payout`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`payout` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `amount` INT NOT NULL,
  `name` TEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`place_payout`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`place_payout` (
  `place_id` INT NOT NULL,
  `payout_id` INT NOT NULL,
  `season_id` INT NOT NULL,
  `game_type_id` INT NOT NULL,
  PRIMARY KEY (`place_id`, `season_id`, `payout_id`, `game_type_id`),
  INDEX `payout_idx` (`payout_id` ASC),
  INDEX `season_idx` (`season_id` ASC),
  INDEX `game_type_idx` (`game_type_id` ASC),
  CONSTRAINT `place`
    FOREIGN KEY (`place_id`)
    REFERENCES `jeopardy`.`place` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `payout`
    FOREIGN KEY (`payout_id`)
    REFERENCES `jeopardy`.`payout` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `season`
    FOREIGN KEY (`season_id`)
    REFERENCES `jeopardy`.`season` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `game_type`
    FOREIGN KEY (`game_type_id`)
    REFERENCES `jeopardy`.`game_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`player_round_result`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`player_round_result` (
  `player_id` INT NOT NULL,
  `round_id` INT NOT NULL,
  `game_id` INT NOT NULL,
  `place_id` INT NULL,
  `payout_id` INT NULL,
  `score` INT NULL,
  PRIMARY KEY (`player_id`, `round_id`, `game_id`),
  INDEX `round_idx` (`round_id` ASC),
  INDEX `game_idx` (`game_id` ASC),
  INDEX `place_idx` (`place_id` ASC),
  INDEX `payout_idx` (`payout_id` ASC),
  CONSTRAINT `player`
    FOREIGN KEY (`player_id`)
    REFERENCES `jeopardy`.`player` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `round`
    FOREIGN KEY (`round_id`)
    REFERENCES `jeopardy`.`round` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `game`
    FOREIGN KEY (`game_id`)
    REFERENCES `jeopardy`.`game` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `place`
    FOREIGN KEY (`place_id`)
    REFERENCES `jeopardy`.`place` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `payout`
    FOREIGN KEY (`payout_id`)
    REFERENCES `jeopardy`.`payout` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`clue_response`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`clue_response` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `clue_id` INT NOT NULL,
  `player_id` INT NOT NULL,
  `round_id` INT NOT NULL,
  `game_id` INT NOT NULL,
  `text` TEXT NULL,
  `correct` INT NULL,
  `order_within_clue` INT NULL,
  `order_within_round` INT NULL,
  `order_within_game` INT NULL,
  `player_score` INT NULL,
  `player_score_impact` INT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `player_id_idx` (`player_id` ASC),
  INDEX `clue_id_idx` (`clue_id` ASC),
  INDEX `round_id_idx` (`round_id` ASC),
  INDEX `game_id_idx` (`game_id` ASC),
  CONSTRAINT `player_id`
    FOREIGN KEY (`player_id`)
    REFERENCES `jeopardy`.`player` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `clue_id`
    FOREIGN KEY (`clue_id`)
    REFERENCES `jeopardy`.`clue` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `round_id`
    FOREIGN KEY (`round_id`)
    REFERENCES `jeopardy`.`round` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `game_id`
    FOREIGN KEY (`game_id`)
    REFERENCES `jeopardy`.`game` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `jeopardy`.`game_round_category`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `jeopardy`.`game_round_category` (
  `game_id` INT NOT NULL,
  `round_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `category_order` INT NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`category_id`, `round_id`, `game_id`),
  INDEX `game_idx` (`game_id` ASC),
  INDEX `round_idx` (`round_id` ASC),
  CONSTRAINT `game`
    FOREIGN KEY (`game_id`)
    REFERENCES `jeopardy`.`game` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `round`
    FOREIGN KEY (`round_id`)
    REFERENCES `jeopardy`.`round` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `category`
    FOREIGN KEY (`category_id`)
    REFERENCES `jeopardy`.`category` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;