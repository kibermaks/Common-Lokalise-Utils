#!/usr/bin/env python

import os
from os import listdir
import shutil
import argparse
import json
import tempfile
import localizable
import plistlib
import lokalise_common

LOCALIZATION_FORMAT = u"\"{0}\" = \"{1}\";\n\n"
LOCALIZATION_GROUP_COMMENT_FORMAT = u"/* {0} */\n"
LOCALIZATION_FILE_NAME = u"Localizable.strings"
LOCALIZATION_SETTINGS_FILE_NAME = u"LocalizedSettings.strings"
LOCALIZATIOS_FOLDER = u"localizations"
LOCALIZATIOS_DEFAULT_FOLDER = u"en.lproj"
LOCALIZATIOS_IGNORE_FOLDER = u"Base.lproj"
LOCALIZATIOS_IGNORE_TRANSLATION_FOLDER = u"af.lproj"

LOCALIZATIOS_UNUSED_TAG = 'unused'

def prepareKeyForVslp(key):
	return key.replace(u"\u2028", u"\u2014")

def prepareValueForVslp(value):
	return value.replace(u"\u2028", u"\n")

def replaceEscapeQuote(value):
	return value.replace("\"", "\\\"")

def mergeLocalization(srcFilePath, destFilePath, cleanMode = False, ignoreFilePath = None):
	srcTranslations = localizable.parse_strings(filename=srcFilePath)
	destTranslations = localizable.parse_strings(filename=destFilePath)

	for key, value in srcTranslations.items():
		if not key in destTranslations:
			destTranslations[key] = value
		else:
			destTranslations[key] = {'comment' : value['comment'], 'value' : destTranslations[key]['value']}

	if cleanMode:
		for key, value in destTranslations.items():
			if not key in srcTranslations:
				del destTranslations[key]

	if ignoreFilePath:
		ignoreTranslations = localizable.parse_strings(filename=ignoreFilePath)
		for key, value in ignoreTranslations.items():
			if value['value'] == 'DO NOT TRANSLATE':
				if key in destTranslations:
					del destTranslations[key]


	resultDict = {}
	for key, value in destTranslations.items():
		prepKey = prepareKeyForVslp(key)
		prepValue = prepareValueForVslp(value['value'])
		if not prepKey in resultDict:
			resultDict[prepKey] = {'comment' : value['comment'], 'value' : prepValue}

	contents = ''
	for key, value in resultDict.items():
		contents += LOCALIZATION_GROUP_COMMENT_FORMAT.format(value['comment'])
		contents += LOCALIZATION_FORMAT.format(key, value['value'])

	with open(destFilePath, "w") as f:
		f.write(contents.encode("utf-8"))

	return len(resultDict)

def prepareLocalizedStrings(srcFilePath):
	srcTranslations = localizable.parse_strings(filename=srcFilePath)

	contents = ''
	for key, value in srcTranslations.items():
		contents += LOCALIZATION_GROUP_COMMENT_FORMAT.format(value['comment'])
		contents += LOCALIZATION_FORMAT.format(key, value['value'])

	with open(srcFilePath, "w") as f:
		f.write(contents.encode("utf-8"))

def prepareForVslp(srcFilePath):
	srcTranslations = localizable.parse_strings(filename=srcFilePath)
	
	resultDict = {}
	for key, value in srcTranslations.items():
		prepKey = prepareKeyForVslp(key)
		prepValue = prepareValueForVslp(value['value'])
		if not prepKey in resultDict:
			resultDict[prepKey] = {'comment' : value['comment'], 'value' : prepValue}

	contents = ''
	for key, value in resultDict.items():
		contents += LOCALIZATION_GROUP_COMMENT_FORMAT.format(value['comment'])
		contents += LOCALIZATION_FORMAT.format(key, value['value'])

	with open(srcFilePath, "w") as f:
		f.write(contents.encode("utf-8"))

def generateLocalizedSettings(directory, outFile, plistKeys):
	resultDict = {}
	settingsFiles = (f for f in listdir(directory) if f.endswith('.plist'))

	for settingsFile in settingsFiles:
		plistPath = os.path.join(directory, settingsFile)
		plistDict = plistlib.readPlist(plistPath)

		if plistDict:
			if 'Title' in plistDict:
				resultDict[plistDict['Title']] = plistDict['Title']

			items = plistDict['Items']
			for dict in items:
				for plistKey in plistKeys:
					if plistKey in dict:
						value = dict[plistKey]
						if isinstance(value, basestring):
							resultDict[value] = value

	settingsContents = ''
	for key, value in resultDict.items():
		settingsContents += LOCALIZATION_GROUP_COMMENT_FORMAT.format('Settings')
		settingsContents += LOCALIZATION_FORMAT.format(replaceEscapeQuote(key), replaceEscapeQuote(value))

	with open(outFile, "w") as f:
		f.write(settingsContents.encode("utf-8"))

def lokaliseImport(lokalise_token, lokalise_project_id, localizationsDir, folder, tags = None, cleanMode = False):
	filePath = os.path.join(localizationsDir, folder, LOCALIZATION_FILE_NAME)
	lokalise_common.lokaliseImport(lokalise_token, lokalise_project_id, filePath, os.path.splitext(folder)[0], tags, cleanMode)

def localization_import(localization_folder, settings_localization_folder, settings_plist_keys, lokalise_token, lokalise_project_id, full_import, tags = None, replace = None):
	TEMP_FOLDER = tempfile.mkdtemp()

	print('Generating Localizable.string...')
	os.system('./agi18n -i {} -o {}'.format("\"{}\"".format(localization_folder), "\"{}\"".format(TEMP_FOLDER)))
	mergedLocalizationFilePath = os.path.join(TEMP_FOLDER, LOCALIZATION_FILE_NAME)
	prepareLocalizedStrings(mergedLocalizationFilePath)

	print('Generating LocalizableSettings.string...')
	outSettingsFilePath = os.path.join(TEMP_FOLDER, LOCALIZATION_SETTINGS_FILE_NAME)
	generateLocalizedSettings(settings_localization_folder, outSettingsFilePath, settings_plist_keys)

	print('Copy project localizations to temp folder...')
	localizationsDir = os.path.join(TEMP_FOLDER, LOCALIZATIOS_FOLDER)
	if os.path.exists(localizationsDir):
		shutil.rmtree(localizationsDir)
	os.makedirs(localizationsDir)

	projectLocalizationFolder = (f for f in listdir(localization_folder) if f.endswith('.lproj'))
	for folder in projectLocalizationFolder:
		if folder != LOCALIZATIOS_IGNORE_FOLDER:
			srcPath = os.path.join(localization_folder, folder)
			destPath = os.path.join(localizationsDir, folder)
			shutil.copytree(srcPath, destPath)

	print('Merge generated localizations...')
	mergeLocalization(outSettingsFilePath, mergedLocalizationFilePath)

	destMergedFilePath = os.path.join(localizationsDir, LOCALIZATIOS_DEFAULT_FOLDER, LOCALIZATION_FILE_NAME)
	
	ignoreTranslationsPath = os.path.join(localizationsDir, LOCALIZATIOS_IGNORE_TRANSLATION_FOLDER, LOCALIZATION_FILE_NAME)
	if os.path.exists(ignoreTranslationsPath):
		print('Merge ignoring unused localizations...')
		keysCount = mergeLocalization(mergedLocalizationFilePath, destMergedFilePath, True, ignoreTranslationsPath)
		print('Merged {} keys'.format(keysCount))
	else:
		shutil.copyfile(mergedLocalizationFilePath, destMergedFilePath)

	if full_import:
		lokaliseImport(lokalise_token, lokalise_project_id, localizationsDir, LOCALIZATIOS_DEFAULT_FOLDER, tags)

		print('Merge localizations...')
		srcPath = os.path.join(localization_folder, LOCALIZATIOS_DEFAULT_FOLDER)
		destPath = os.path.join(localizationsDir, LOCALIZATIOS_DEFAULT_FOLDER)
		shutil.rmtree(destPath)
		shutil.copytree(srcPath, destPath)
		keysCount = mergeLocalization(mergedLocalizationFilePath, destMergedFilePath)
		print('Merged {} keys'.format(keysCount))

		unusedTags = (tags + [LOCALIZATIOS_UNUSED_TAG]) if tags != None else [LOCALIZATIOS_UNUSED_TAG]
		lokaliseImport(lokalise_token, lokalise_project_id, localizationsDir, LOCALIZATIOS_DEFAULT_FOLDER, unusedTags)

		localizationFolder = (f for f in listdir(localizationsDir) if f.endswith('.lproj'))
		for folder in localizationFolder:
			if folder != LOCALIZATIOS_IGNORE_FOLDER and folder != LOCALIZATIOS_DEFAULT_FOLDER:
				lokaliseImport(lokalise_token, lokalise_project_id, localizationsDir, folder, tags)
	else:
		lokaliseImport(lokalise_token, lokalise_project_id, localizationsDir, LOCALIZATIOS_DEFAULT_FOLDER, tags)

	shutil.rmtree(TEMP_FOLDER)

def prepareVslpKeyForApp(key):
	return key.replace(u"\u2014", u"\u2028").replace(u"\u2012", u"\n")

def prepareVslpValueForApp(value):
	return value.replace(u"\u2014", u"\n").replace(u"\u2012", u"\n")

def prepareVslpForApp(srcFilePath):
	srcTranslations = localizable.parse_strings(filename=srcFilePath)
	
	resultDict = {}
	for key, value in srcTranslations.items():
		prepKey = prepareVslpKeyForApp(key)
		prepValue = prepareVslpValueForApp(value['value'])
		if not prepKey in resultDict:
			resultDict[prepKey] = {'comment' : value['comment'], 'value' : prepValue}

	contents = ''
	for key, value in resultDict.items():
		contents += LOCALIZATION_GROUP_COMMENT_FORMAT.format(value['comment'])
		contents += LOCALIZATION_FORMAT.format(key, value['value'])

	with open(srcFilePath, "w") as f:
		f.write(contents.encode("utf-8"))

def localization_export(localization_folder, lokalise_token, lokalise_project_id):
	print('Removing local localizations...')
	localizationFolders = (f for f in listdir(localization_folder) if f.endswith('.lproj'))
	for folder in localizationFolders:
		if folder != LOCALIZATIOS_IGNORE_FOLDER:
			folderPath = os.path.join(localization_folder, folder)
			shutil.rmtree(folderPath)

	lokalise_common.lokaliseExport(lokalise_token, lokalise_project_id, "strings", localization_folder)
