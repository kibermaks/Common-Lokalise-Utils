import os

def lokaliseImport(lokalise_token, lokalise_project_id, file_path, localization_code, tags, cleanMode = False):
	lokaliseCommand = 'lokalise --token {} import {} --file {} --lang_iso {}'.format(lokalise_token, lokalise_project_id, file_path, localization_code)
	if tags:
		lokaliseCommand += " --tags {}".format(",".join(tags))
	if cleanMode:
		lokaliseCommand += " --cleanup_mode 1"
	print(lokaliseCommand)
	os.system(lokaliseCommand)

def lokaliseExport(lokalise_token, lokalise_project_id, localization_type, localization_folder):
	lokaliseCommand = 'lokalise --token {} export {} --type {} --export_empty skip --unzip_to {}'.format(lokalise_token, lokalise_project_id, localization_type, "\"{}\"".format(localization_folder))
	print(lokaliseCommand)
	os.system(lokaliseCommand)