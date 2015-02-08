#!/usr/bin/env python
# make.py
# Copyright (C) 2015 by CJP
#
# This file is part of Amiko Pay.
#
# Amiko Pay is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Amiko Pay is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.

pages = \
[
	#Name in menu , filename base, URL in menu
	("Home"       , "index"      , "."),
	("Download"   , "download"   , "download.html"),
	("Resources"  , "resources"  , "resources.html"),
	("News"       , "news"       , "news.html"),
	("Contact"    , "contact"    , "contact.html"),
]

with open("src/template.html", "rb") as f:
	template = f.read()

for menuName, filenameBase, URL in pages:
	with open("src/" + filenameBase + ".html", "rb") as f:
		body = f.read()

	menu = ""
	for menuName2, filenameBase2, URL2 in pages:
		if menuName2 == menuName:
			menu += '            <li class="active"><a href="%s">%s</a></li>\n' % \
				(URL2, menuName2)
		else:
			menu += '            <li><a href="%s">%s</a></li>\n' % \
				(URL2, menuName2)

	with open(filenameBase + ".html", "wb") as f:
		f.write(template % (menu, body))

