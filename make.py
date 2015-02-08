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
	#Name in menu, filename base, URL in menu
	("Home"      , "index"      , "."),
	("Download"  , "download"   , "download.html"),
	("News"      , "news"       , "news.html"),
	("Contact"   , "contact"    , "contact.html"),
]


for menuName, filenameBase, URL in pages:
	with open(filenameBase + ".src.html", "rb") as f:
		body = f.read()

	with open(filenameBase + ".html", "wb") as f:
		f.write("""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="icon" href="favicon.ico">

    <title>Amiko Pay</title>

    <!-- Bootstrap core CSS -->
    <link href="dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Custom styles for this website -->
    <link href="body.css" rel="stylesheet">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>

  <body>

    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href=".">Amiko Pay</a>
        </div>
        <div id="navbar" class="collapse navbar-collapse">
          <ul class="nav navbar-nav">
""")

		for menuName2, filenameBase2, URL2 in pages:
			if menuName2 == menuName:
				f.write('            <li class="active"><a href="%s">%s</a></li>\n' % \
					(URL2, menuName2))
			else:
				f.write('            <li><a href="%s">%s</a></li>\n' % \
					(URL2, menuName2))

		f.write("""          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container">

      <div class="amikobody">
""")

		f.write(body)


		f.write("""      </div>
    </div><!-- /.container -->


    <!-- Bootstrap core JavaScript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="jquery.min.js"></script>
    <script src="dist/js/bootstrap.min.js"></script>
  </body>
</html>""")

