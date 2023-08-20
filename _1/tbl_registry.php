<?php

## Select Records from Mysql ***********************************************************************8

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "blb_registry";

// Create connection
$conn_mysql = new mysqli($servername, $username, $password, $dbname);
if ($conn_mysql->connect_error) {
  die("Connection failed: " . $conn_mysql->connect_error);
}

//Select Data
$sql = "SELECT * FROM tbl_registry ORDER BY id ASC LIMIT 10";
$result = $conn_mysql->query($sql);
$conn_mysql->close();

//No. of Records
echo "No. Records:- ".$result->num_rows."<br><br>";

//Connect to Postgres
$host = "host=127.0.0.1";
$port = "port=5432";
$db_blb = "dbname = BLB-14";
$credentials = "user=openpg password=openpgpwd";

$db_conn = pg_connect("$host $port $db_blb $credentials");
if(!$db_conn) {
	echo "Error : Unable to open postgres database <br><br>";
} else {
    echo "Opened postgres database successfully<br><br>";
}


//Insert into Postgres
while($row = $result->fetch_assoc()) {
	//echo "id: " . $row["id"]. " - Name: " . $row["firstname"]. " " . $row["lastname"]. "<br>";
	$id = $row['id'];  $file_no = str_replace('\0', '', trim($row['file_no']));  $file_name = str_replace('\0', '', trim($row['file_name'])); 
	$location = str_replace('\0', '', trim($row['location'])); $postal_address = str_replace('\0', '', trim($row['postal_address'])); 
	$telephone = str_replace('\0', '', trim($row['telephone']));  $email = str_replace('\0', '', trim($row['email'])); 
	$nationality = str_replace('\0', '', trim($row['nationality']));  
	$if_other_specify_nationality = str_replace('\0', '', trim($row['if_other_specify_nationality'])); 
	$purpose_of_land = str_replace('\0', '', trim($row['purpose_of_land'])); 
	$if_other_specify_purpose =  str_replace('\0', '', trim($row['if_other_specify_purpose'])); 
	$nature_of_business = str_replace('\0', '', trim($row['nature_of_business']));  
	$date_business_established = str_replace('\0', '', trim($row['date_business_established'])); 
	$director_trustee_1 = str_replace('\0', '', trim($row['director_trustee_1']));  $share_holding_1 = str_replace('\0', '', trim($row['share_holding_1'])); 
	$director_trustee_2 = str_replace('\0', '', trim($row['director_trustee_2'])); $share_holding_2 = str_replace('\0', '', trim($row['share_holding_2'])); 
	$director_trustee_3 = str_replace('\0', '', trim($row['director_trustee_3'])); $share_holding_3 = str_replace('\0', '', trim($row['share_holding_3'])); 
	$block_no = str_replace('\0', '', trim($row['block_no'])); $plot_no = str_replace('\0', '', trim($row['plot_no'])); 
	$approximate_area = str_replace('\0', '', trim($row['approximate_area'])); $district = str_replace('\0', '', trim($row['district'])); 
	$county = str_replace('\0', '', trim($row['county']));  $sub_county = str_replace('\0', '', trim($row['sub_county'])); 
	$lc_zone = str_replace('\0', '', trim($row['lc_zone']));  $parish =  str_replace('\0', '', trim($row['parish'])); 
	$value_of_project = str_replace('\0', '', trim($row['value_of_project'])); $type_of_tenure = str_replace('\0', '', trim($row['type_of_tenure'])); 
	$details_of_tenure = str_replace('\0', '', trim($row['details_of_tenure'])); $development_activity = str_replace('\0', '', trim($row['development_activity'])); 
	$joint_ownership = str_replace('\0', '', trim($row['joint_ownership']));  $tenants_in_common = str_replace('\0', '', trim($row['tenants_in_common'])); 
	$date_of_application = str_replace('\0', '', trim($row['date_of_application']));  
	$application_receipt_no = str_replace('\0', '', trim($row['application_receipt_no'])); 
	$application_fees = str_replace('\0', '', trim($row['application_fees']));  $relationship_manager = str_replace('\0', '', trim($row['relationship_manager'])); 
	$recommenders_name = str_replace('\0', '', trim($row['recommenders_name']));  
	$recommenders_profession = str_replace('\0', '', trim($row['recommenders_profession'])); 
	$recommenders_address = str_replace('\0', '', trim($row['recommenders_address'])); $file_status = str_replace('\0', '', trim($row['file_status'])); 
	$land_title = str_replace('\0', '', trim($row['land_title'])); $passport_photo = str_replace('\0', '', trim($row['passport_photo'])); 
	$land_house_photo = str_replace('\0', '', trim($row['land_house_photo'])); $ownership_documents = str_replace('\0', '', trim($row['ownership_documents'])); 
	$deed_print = str_replace('\0', '', trim($row['deed_print'])); $lease_offer = str_replace('\0', '', trim($row['lease_offer'])); 
	$receipts = str_replace('\0', '', trim($row['receipts'])); $lease_agreement = str_replace('\0', '', trim($row['lease_agreement'])); 
	$sketch_map = str_replace('\0', '', trim($row['sketch_map']));  $other_documents = str_replace('\0', '', trim($row['other_documents'])); 
	$type_of_applicant = str_replace('\0', '', trim($row['type_of_applicant'])); $minute_number = str_replace('\0', '', trim($row['minute_number'])); 
	$date_of_minute = str_replace('\0', '', trim($row['date_of_minute'])); $duration = str_replace('\0', '', trim($row['duration'])); 
	$start_date = str_replace('\0', '', trim($row['start_date']));  $kcc_start_date = str_replace('\0', '', trim($row['kcc_start_date'])); 
	$premium = str_replace('\0', '', trim($row['premium']));  $annual_rent = str_replace('\0', '', trim($row['annual_rent'])); 
	$revision_period_from = str_replace('\0', '', trim($row['revision_period_from']));  
	$revision_period_after =  str_replace('\0', '', trim($row['revision_period_after'])); 
	$name_of_witness_and_address = str_replace('\0', '', trim($row['name_of_witness_and_address']));  
	$lease_status = str_replace('\0', '', trim($row['lease_status'])); 
	$volume_number = str_replace('\0', '', trim($row['volume_number']));  $folio_number = str_replace('\0', '', trim($row['folio_number'])); 
	$city = str_replace('\0', '', trim($row['city'])); $duration_of_term = str_replace('\0', '', trim($row['duration_of_term'])); 
	$commencement_of_term = str_replace('\0', '', trim($row['commencement_of_term']));  $instrument_number = str_replace('\0', '', trim($row['instrument_number'])); 
	$registration_date = str_replace('\0', '', trim($row['registration_date']));  
	$date_of_certificate_issue = str_replace('\0', '', trim($row['date_of_certificate_issue'])); 
	$remarks_on_file_disputes = str_replace('\0', '', trim($row['remarks_on_file_disputes']));  
	$certificate_of_title_status = str_replace('\0', '', trim($row['certificate_of_title_status'])); 
	$informational_note = str_replace('\0', '', trim($row['informational_note']));  $migrated_flag = str_replace('\0', '', trim($row['migrated_flag'])); 
	$date_migration = str_replace('\0', '', trim($row['date_migration']));  $file_tracker_flag = str_replace('\0', '', trim($row['file_tracker_flag'])); 
	$accessed_by = str_replace('\0', '', trim($row['accessed_by']));  $migrated_msdynamics = str_replace('\0', '', trim($row['migrated_msdynamics'])); 
	$modified_status = str_replace('\0', '', trim($row['modified_status']));  $date_migrated_msdy = str_replace('\0', '', trim($row['date_migrated_msdy'])); 
	$file_cleaned = str_replace('\0', '', trim($row['file_cleaned']));  $last_updated = str_replace('\0', '', trim($row['last_updated'])); 
	$le_card = str_replace('\0', '', trim($row['le_card']));

	//name
	$name = $file_no." (". $file_name .")";

	$sql = "INSERT INTO blb_client_blb_db2_tbl_registry (id,name,file_no,file_name,location,postal_address,telephone,email,nationality,if_other_specify_nationality,
								purpose_of_land,if_other_specify_purpose,nature_of_business,date_business_established,director_trustee_1,share_holding_1,director_trustee_2,
								share_holding_2,director_trustee_3,share_holding_3,block_no,plot_no,approximate_area,district,county,sub_county,lc_zone,parish,value_of_project,
								type_of_tenure,details_of_tenure,development_activity,joint_ownership,tenants_in_common,date_of_application,application_receipt_no,
								application_fees,relationship_manager,recommenders_name,recommenders_profession,recommenders_address,file_status,land_title,passport_photo,
								land_house_photo,ownership_documents,deed_print,lease_offer,receipts,lease_agreement,sketch_map,other_documents,type_of_applicant,minute_number,
								date_of_minute,duration,start_date,kcc_start_date,premium,annual_rent,revision_period_from,revision_period_after,name_of_witness_and_address,
								lease_status,volume_number,folio_number,city,duration_of_term,commencement_of_term,instrument_number,registration_date,date_of_certificate_issue,
								remarks_on_file_disputes,certificate_of_title_status,informational_note,migrated_flag,date_migration,file_tracker_flag,accessed_by,
								migrated_msdynamics,modified_status,date_migrated_msdy,file_cleaned,last_updated,le_card) 
					VALUES 
					( '$id', '$name',
						'$file_no', '$file_name', '$location', '$postal_address', '$telephone', '$email', '$nationality', '$if_other_specify_nationality', 
						'$purpose_of_land', '$if_other_specify_purpose', '$nature_of_business', '$date_business_established', '$director_trustee_1', '$share_holding_1', 
						'$director_trustee_2', '$share_holding_2', '$director_trustee_3', '$share_holding_3', '$block_no', '$plot_no', '$approximate_area', 
						'$district', '$county', '$sub_county', '$lc_zone', '$parish', '$value_of_project', '$type_of_tenure', '$details_of_tenure', '$development_activity', 
						'$joint_ownership', '$tenants_in_common', '$date_of_application', '$application_receipt_no', '$application_fees', '$relationship_manager', 
						'$recommenders_name', '$recommenders_profession', '$recommenders_address', '$file_status', '$land_title', '$passport_photo', '$land_house_photo', 
						'$ownership_documents', '$deed_print', '$lease_offer', 
					  '$receipts', '$lease_agreement', '$sketch_map', '$other_documents', '$type_of_applicant', '$minute_number', '$date_of_minute', '$duration', 
					  '$start_date', '$kcc_start_date', '$premium', '$annual_rent', '$revision_period_from', '$revision_period_after', '$name_of_witness_and_address', 
					  '$lease_status', '$volume_number', '$folio_number', '$city', '$duration_of_term', '$commencement_of_term', '$instrument_number', 
						'$registration_date', '$date_of_certificate_issue', '$remarks_on_file_disputes', '$certificate_of_title_status', '$informational_note', 
					  '$migrated_flag', '$date_migration', '$file_tracker_flag', '$accessed_by', '$migrated_msdynamics', '$modified_status', '$date_migrated_msdy', 
					  '$file_cleaned', '$last_updated', '$le_card')";

	$insert_result = pg_query($db_conn, $sql);
	if(!$insert_result) {
		echo pg_last_error($db_conn);
	} else {
	    echo "Records insert:- ".$row["id"]."<br>";
	}


	//Insert into Clients Table
	$sql2 ="INSERT INTO blb_client_blb_client (old_registryfile_id,name,file_no,client_name,location)
      		VALUES ( '$id', '$name', '$file_no', '$file_name', '$location')";

  $insert_result2 = pg_query($db_conn, $sql2);
	if(!$insert_result2) {
		echo pg_last_error($db_conn);
	} else {
	    echo "Records insert old_registryfile_id:- ".$row["id"]."<br><br>";
	}



	   
}

//Close postgres-db connection
pg_close($db_conn);








?>