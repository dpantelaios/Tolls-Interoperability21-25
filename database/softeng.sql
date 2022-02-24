SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";
CREATE TABLE `charge` (`operator_ID` char(2) NOT NULL, `operator_ID2` char(2) NOT NULL, `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),  `amount` float NOT NULL,  `pass_ID` varchar(255) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE `chargesum` (`amount` float DEFAULT NULL, `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),  `settled` bit(1) NOT NULL DEFAULT b'0',  `operator_ID` char(2) NOT NULL,  `operator_ID2` char(2) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE `operator` (  `operator_ID` char(2) NOT NULL,  `operator_name` varchar(50) DEFAULT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE `pass` (  `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),  `charge` float DEFAULT NULL,  `station_ID` varchar(255) NOT NULL,  `vehicle_ID` varchar(255) NOT NULL,  `pass_ID` varchar(255) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE `station` (  `station_ID` varchar(255) NOT NULL,  `station_name` varchar(255) DEFAULT NULL,  `operator_ID` char(2) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE `vehicle` (  `tag_ID` varchar(255) NOT NULL,  `vehicle_ID` varchar(255) NOT NULL,  `license_year` int(4) DEFAULT NULL,  `balance` float DEFAULT NULL,  `operator_ID` char(2) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE `user` (  `type` varchar(50) DEFAULT NULL,  `username` varchar(30) NOT NULL,  `password` varchar(30) DEFAULT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
ALTER TABLE `charge`  ADD PRIMARY KEY (`pass_ID`),  ADD KEY `FKCharge128726` (`operator_ID`),  ADD KEY `FKCharge573658` (`operator_ID2`);
ALTER TABLE `chargesum`  ADD PRIMARY KEY (`timestamp`,`operator_ID`,`operator_ID2`),  ADD KEY `FKChargeSum310105` (`operator_ID`),  ADD KEY `FKChargeSum865172` (`operator_ID2`);
ALTER TABLE `operator`  ADD PRIMARY KEY (`operator_ID`);
ALTER TABLE `pass`  ADD PRIMARY KEY (`pass_ID`),  ADD KEY `FKPass796425` (`vehicle_ID`),  ADD KEY `FKPass821180` (`station_ID`);
ALTER TABLE `station`  ADD PRIMARY KEY (`station_ID`),  ADD KEY `FKStation557939` (`operator_ID`);
ALTER TABLE `vehicle`  ADD PRIMARY KEY (`vehicle_ID`),  ADD KEY `FKVehicle991332` (`operator_ID`);
ALTER TABLE `user`  ADD PRIMARY KEY (`username`);
ALTER TABLE `charge`  ADD CONSTRAINT `FKCharge128726` FOREIGN KEY (`operator_ID`) REFERENCES `operator` (`operator_ID`) ON DELETE CASCADE ON UPDATE CASCADE,  ADD CONSTRAINT `FKCharge281092` FOREIGN KEY (`pass_ID`) REFERENCES `pass` (`pass_ID`) ON DELETE CASCADE ON UPDATE CASCADE,  ADD CONSTRAINT `FKCharge573658` FOREIGN KEY (`operator_ID2`) REFERENCES `operator` (`operator_ID`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `chargesum`  ADD CONSTRAINT `FKChargeSum310105` FOREIGN KEY (`operator_ID`) REFERENCES `operator` (`operator_ID`) ON DELETE CASCADE ON UPDATE CASCADE,  ADD CONSTRAINT `FKChargeSum865172` FOREIGN KEY (`operator_ID2`) REFERENCES `operator` (`operator_ID`) ON DELETE CASCADE ON UPDATE CASCADE ;
ALTER TABLE `pass`  ADD CONSTRAINT `FKPass796425` FOREIGN KEY (`vehicle_ID`) REFERENCES `vehicle` (`vehicle_ID`) ON DELETE CASCADE ON UPDATE CASCADE,  ADD CONSTRAINT `FKPass821180` FOREIGN KEY (`station_ID`) REFERENCES `station` (`station_ID`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `station`  ADD CONSTRAINT `FKStation557939` FOREIGN KEY (`operator_ID`) REFERENCES `operator` (`operator_ID`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE `vehicle`  ADD CONSTRAINT `FKVehicle991332` FOREIGN KEY (`operator_ID`) REFERENCES `operator` (`operator_ID`) ON DELETE CASCADE ON UPDATE CASCADE;
INSERT INTO operator VALUES('AO','aodos'),('OO','olympia_odos'),('NE','nea_odos'),('GF','gefyra'),('KO','kentriki_odos'),('EG','egnatia'),('MR', 'moreas');
CREATE TRIGGER PASS_TO_CHARGE
	AFTER INSERT
    ON pass FOR EACH ROW
 BEGIN
	DECLARE ID1 CHAR(2);
	DECLARE ID2 CHAR(2);
    SET ID1 = (SELECT DISTINCT operator_ID
        FROM station
        WHERE NEW.station_ID=station.station_ID);
    SET ID2 = (SELECT DISTINCT operator_ID
        FROM vehicle
        WHERE NEW.vehicle_ID=vehicle.vehicle_ID);
	IF ID1<>ID2 THEN 
		INSERT INTO charge VALUES(ID2,ID1,NEW.pass_time,NEW.charge,NEW.pass_ID);
	END IF;
END
COMMIT;
