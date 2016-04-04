-- MySQL dump 10.13  Distrib 5.6.26, for osx10.10 (x86_64)
--
-- Host: localhost    Database: db_project
-- ------------------------------------------------------
-- Server version	5.6.26

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `following`
--

DROP TABLE IF EXISTS `following`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `following` (
  `followee` varchar(35) NOT NULL,
  `follower` varchar(35) NOT NULL,
  KEY `followee` (`followee`),
  KEY `follower` (`follower`),
  CONSTRAINT `following_ibfk_1` FOREIGN KEY (`followee`) REFERENCES `User` (`email`),
  CONSTRAINT `following_ibfk_2` FOREIGN KEY (`follower`) REFERENCES `User` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `forum`
--

DROP TABLE IF EXISTS `forum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `forum` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `short_name` varchar(35) NOT NULL,
  `user` varchar(35) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_key_forum` (`name`),
  KEY `user` (`user`),
  KEY `short_name` (`short_name`),
  CONSTRAINT `forum_ibfk_1` FOREIGN KEY (`user`) REFERENCES `User` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `post`
--

DROP TABLE IF EXISTS `post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `post` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `thread` int(10) NOT NULL,
  `message` varchar(1000) NOT NULL,
  `user` varchar(35) NOT NULL,
  `forum` varchar(35) NOT NULL,
  `parent` int(10) NOT NULL DEFAULT '0',
  `isApproved` tinyint(1) NOT NULL DEFAULT '0',
  `isHighlighted` tinyint(1) NOT NULL DEFAULT '0',
  `isEdited` tinyint(1) NOT NULL DEFAULT '0',
  `isSpam` tinyint(1) NOT NULL DEFAULT '0',
  `isDeleted` tinyint(1) NOT NULL DEFAULT '0',
  `likes` int(10) NOT NULL DEFAULT '0',
  `dislikes` int(10) NOT NULL DEFAULT '0',
  `points` int(10) NOT NULL DEFAULT '0',
  `path` varchar(350) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `forum` (`forum`),
  KEY `thread` (`thread`),
  KEY `user` (`user`),
  CONSTRAINT `post_ibfk_1` FOREIGN KEY (`forum`) REFERENCES `Forum` (`short_name`),
  CONSTRAINT `post_ibfk_2` FOREIGN KEY (`thread`) REFERENCES `Thread` (`id`),
  CONSTRAINT `post_ibfk_3` FOREIGN KEY (`user`) REFERENCES `User` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=18448 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `thread`
--

DROP TABLE IF EXISTS `thread`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `thread` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `forum` varchar(35) NOT NULL,
  `title` varchar(100) NOT NULL,
  `isClosed` tinyint(1) NOT NULL,
  `user` varchar(35) NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `message` varchar(4500) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `isDeleted` tinyint(1) NOT NULL,
  `likes` int(10) NOT NULL,
  `dislikes` int(10) NOT NULL,
  `points` int(10) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `forum` (`forum`),
  KEY `user` (`user`),
  CONSTRAINT `thread_ibfk_1` FOREIGN KEY (`forum`) REFERENCES `Forum` (`short_name`),
  CONSTRAINT `thread_ibfk_2` FOREIGN KEY (`user`) REFERENCES `User` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=10001 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `thread_subscr`
--

DROP TABLE IF EXISTS `thread_subscr`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `thread_subscr` (
  `user` varchar(35) NOT NULL,
  `thread` int(10) NOT NULL,
  KEY `user` (`user`),
  KEY `thread` (`thread`),
  CONSTRAINT `thread_subscr_ibfk_1` FOREIGN KEY (`user`) REFERENCES `User` (`email`),
  CONSTRAINT `thread_subscr_ibfk_2` FOREIGN KEY (`thread`) REFERENCES `Thread` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(35) NOT NULL,
  `about` varchar(4300) DEFAULT NULL,
  `isAnonymous` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `username` varchar(25) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=100001 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-04-04 12:54:08
