import sublime, sublime_plugin
import zipfile
import os

def get_classes_list(path):
	if path.endswith(".zip") or path.endswith(".jar"):
		zipF = zipfile.ZipFile(path, "r")
		classesList = zipF.namelist()
		zipF.close()
		return classesList
	else:
		classesList = []
		for root, dirs, files in os.walk(path):
			for fname in files:
				if fname.endswith(".zip") or fname.endswith(".jar"):
					classesList = classesList + get_classes_list(root+"/"+fname)
				elif fname.endswith(".class") or fname.endswith(".java"):
					classesList.append((root+"/"+fname)[len(path):])
		return classesList

def is_class_exists(className, fileName):
	return fileName.endswith("/"+className+".java") \
		or fileName.endswith("\\"+className+".java") \
		or fileName.endswith("/"+className+".class") \
		or fileName.endswith("\\"+className+".class")

class JavaAddImportCommand(sublime_plugin.TextCommand):
	classesList = []
	lastImportPath = []

	def run(self, edit):
		settings = self.view.settings()
		if not settings.has("java_import_path"):
			settings = sublime.load_settings("JavaImports.sublime-settings")
			if not settings.has("java_import_path"):
				sublime.error_message("You must first define \"java_import_path\" in your settings")
				return
		if len(settings.get("java_import_path")) == 0:
			sublime.error_message("You must first define \"java_import_path\" in your settings")
			return

		importPath = settings.get("java_import_path")
		if importPath != self.lastImportPath:
			self.classesList = []
			self.lastImportPath = importPath
			for path in importPath:
				self.classesList = self.classesList + get_classes_list(path)

		def onDone(className):
			results = []
			for name in self.classesList:
				if is_class_exists(className, name):
					result = name \
						.replace("/",".") \
						.replace("\\",".") \
						.replace(".java","") \
						.replace(".class", "")
					if result.startswith("."):
						result = result[1:]
					results.append(result)

			def finishUp(index):
				if index == -1:
					return
				self.view.run_command("java_add_import_insert", {"classpath":results[index]})

			if len(results) == 1:
				finishUp(0)
			elif len(results) > 1:
				self.view.window().show_quick_panel(results, finishUp)
			else:
				sublime.error_message("There is no such class in \"java_import_path\"")

		allEmpty = True
		for sel in self.view.sel():
			if sel.empty():
				continue
			onDone(self.view.substr(sel))
			allEmpty = False
		if allEmpty:
			self.view.window().show_input_panel("Class name: ", "", onDone, None, None)

class JavaAddImportInsertCommand(sublime_plugin.TextCommand):
	def run(self, edit, classpath):
		for i in range(0, 10000):
			point = self.view.text_point(i, 0)
			region = self.view.line(point)
			line = self.view.substr(region)
			if len(line) == 0: continue

			if "import" in line:
				self.view.insert(edit, point, "import "+classpath+";\n")
				break

			if line[0] == "@" or "class " in line:
				self.view.insert(edit, point, "import "+classpath+";\n\n")
				break