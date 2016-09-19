#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
#import httplib
import sys
import re
import os
import psycopg2
import psycopg2.extras
import db_config as config
import math
import tempfile

def generate_gnuplot_graph_lines_by_day():
	for line_name in lines:
		line=lines[line_name]
		line["graphs"]={}
		if len(line["ways"]) == 0 or len(line["node_lists"]) == 0:
			continue

		for way_id in line["ways"]:
			# Пропускаем линии, в которых нет пролётов (например из двух точек, одна из которых не имеет 'ref')
			if not way_id in line["prolet_lists"]:
				continue

			if config.debug:
				line_data_file= config.graph_path+"/line-%d.txt"%way_id
				line_gnuplot_cmd_file=config.graph_path+"/line-%d.plt"%way_id
				line_result_png_file=config.graph_path+"/line-%d.png"%way_id
			else:
				line_data_file=tempfile.mkstemp(suffix=".txt",prefix="gnuplot-%d-"%way_id,dir=config.graph_path)[1]
				line_gnuplot_cmd_file=tempfile.mkstemp(suffix=".plt",prefix="gnuplot-%d-"%way_id,dir=config.graph_path)[1]
				line_result_png_file=tempfile.mkstemp(suffix=".png",prefix="gnuplot-%d-"%way_id,dir=config.graph_path)[1]

			data_file=open(line_data_file,"w+")
			cmd_file=open(line_gnuplot_cmd_file,"w+")

			prolet_list=line["prolet_lists"][way_id]["prolet_list"]
			graph_x=1024
			graph_y=600
			if len(prolet_list) > 20:
				graph_x=len(prolet_list)*50
				
			cmd_file.write("""set terminal  png size %(graph_x)d,%(graph_y)d
set output '%(output_file)s'
set xlabel "Дни"
set ylabel "Количество объектов в базе"
set key top left
""" % {"graph_x":graph_x, "graph_y":graph_y, "output_file":line_result_png_file})

			x=0
			for (i=0;i<20;i++):
				if x==0:
					data_file.write(""""1"	%(x)f	%(ele)f\n""" % {"ref":prolet["node1"]["tags"]["ref"], "x":x, "ele":prolet["node1"]["ele"]})
					cmd_file.write("""set label "%(ref)s" at %(x)f,%(ele)f\n""" % {"ref":re.sub(r'["]',r'',prolet["node1"]["tags"]["ref"]), "x":x, "ele":prolet["node1"]["ele"]})
				x+=prolet["dist"]
				data_file.write(""""%(ref)s"	%(x)f	%(ele)f\n""" % {"ref":prolet["node2"]["tags"]["ref"], "x":x, "ele":prolet["node2"]["ele"]})
				cmd_file.write("""set label "%(ref)s" at %(x)f,%(ele)f\n""" % {"ref":re.sub(r'["]',r'',prolet["node2"]["tags"]["ref"]), "x":x, "ele":prolet["node2"]["ele"]})
			# Подписи по оси X:
			cmd_file.write("""
 set xtics (""")
			x=0
			for prolet in prolet_list:
				if x==0:
					cmd_file.write(""""0" 0,""" )
				x+=prolet["dist"]
				cmd_file.write(""""%(prolet).0f" %(x)f""" % {"prolet":prolet["dist"], "x":x})
				# В самом конце списка запятую не ставим:
				if prolet != prolet_list[-1]:
					cmd_file.write(", ")

			cmd_file.write(")\n")

			cmd_file.write("""
set grid
plot '%(line_data_file)s'using 2:3 with linespoints lw 1 lt rgb 'purple' title 'Профиль линии "%(line_name)s"'
		""" % {"line_data_file":line_data_file, "line_name":line_name})
			data_file.close()
			cmd_file.close()
			if config.debug:
				print('/usr/bin/gnuplot {0} &> /dev/null'.format(line_gnuplot_cmd_file))
			os.system('/usr/bin/gnuplot "{0}" &> /dev/null'.format(line_gnuplot_cmd_file))

			line["graphs"][way_id]=config.graph_path+"/"+line_result_png_file.split(os.sep)[-1]


def get_num_of_tower():
	try:
		sql="""select node_id from node_tags where cast(node_id as text) || '-' || cast(version as text) in ( select cast(node_id as text) || '-' || cast(max(version) as text) as tt from nodes group by node_id) and node_id in (select node_id from node_tags where (k='power' and v='tower')) and k='ref' group by node_id"""

		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items

def get_num_of_station_as_node():
	try:
		sql="""select node_id from node_tags where cast(node_id as text) || '-' || cast(version as text) in ( select cast(node_id as text) || '-' || cast(max(version) as text) as tt from nodes group by node_id) and node_id in (select node_id from node_tags where (k='power' and v='station')) and k='name' group by node_id"""

		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items

def get_num_of_tp_as_node():
	try:
		sql="""select node_id from node_tags where cast(node_id as text) || '-' || cast(version as text) in ( select cast(node_id as text) || '-' || cast(max(version) as text) as tt from nodes group by node_id) and node_id in (select node_id from node_tags where (k='power' and v='sub_station')) and k='ref' group by node_id"""

		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items

def get_num_of_lines_as_ways():
	try:
		sql="""select way_id from way_tags where cast(way_id as text) || '-' || cast(version as text) in ( select cast(way_id as text) || '-' || cast(max(version) as text) as tt from way_tags group by way_id) and way_id in (select way_id from way_tags where k='power' and (v='line' or v='cable')) and k='name' group by way_id"""
		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items

def get_num_of_tp_as_ways():
	try:
		sql="""select way_id from way_tags where cast(way_id as text) || '-' || cast(version as text) in ( select cast(way_id as text) || '-' || cast(max(version) as text) as tt from way_tags group by way_id) and way_id in (select way_id from way_tags where k='power' and v='sub_station') and k='ref' group by way_id"""
		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items

def get_num_of_station_as_ways():
	try:
		sql="""select way_id from way_tags where cast(way_id as text) || '-' || cast(version as text) in ( select cast(way_id as text) || '-' || cast(max(version) as text) as tt from way_tags group by way_id) and way_id in (select way_id from way_tags where k='power' and v='station') and k='name' group by way_id"""
		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items


def get_num_of_lines_as_relations():
	try:
		sql="""select relation_id,max(version) as version from relation_members where member_type='Way' and member_id in (select way_id from way_nodes where cast(way_id as text) || '-' || cast(version as text) in (select cast(way_id as text) || '-' || cast(max(version) as text) from way_nodes group by way_id) group by way_id) and cast(relation_id as text) || '-' || cast(version as text) in (select cast(relation_id as text) || '-' || cast(version as text) from relation_tags where  cast(relation_id as text) || '-' || cast(version as text) in (select cast(relation_id as text) || '-' || cast(max(version) as text) from relation_tags group by relation_id) and k='power' and (v='line' or v='cable')) group by relation_id"""
		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items


def get_num_of_station_as_relations():
	try:
		sql="""select relation_id,max(version) as version from relation_members where member_type='Way' and member_id in (select way_id from way_nodes where cast(way_id as text) || '-' || cast(version as text) in (select cast(way_id as text) || '-' || cast(max(version) as text) from way_nodes group by way_id) group by way_id) and cast(relation_id as text) || '-' || cast(version as text) in (select cast(relation_id as text) || '-' || cast(version as text) from relation_tags where  cast(relation_id as text) || '-' || cast(version as text) in (select cast(relation_id as text) || '-' || cast(max(version) as text) from relation_tags group by relation_id) and k='power' and v='station') group by relation_id"""
		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items


def get_num_of_tp_as_relations():
	try:
		sql="""select relation_id,max(version) as version from relation_members where member_type='Way' and member_id in (select way_id from way_nodes where cast(way_id as text) || '-' || cast(version as text) in (select cast(way_id as text) || '-' || cast(max(version) as text) from way_nodes group by way_id) group by way_id) and cast(relation_id as text) || '-' || cast(version as text) in (select cast(relation_id as text) || '-' || cast(version as text) from relation_tags where  cast(relation_id as text) || '-' || cast(version as text) in (select cast(relation_id as text) || '-' || cast(max(version) as text) from relation_tags group by relation_id) and k='power' and v='sub_station') group by relation_id"""
		if config.debug==True:
			print("sql=%s" % sql)
		cur.execute(sql)
		items=cur.fetchall()
	except:
		print ("I am unable fetch data from db");sys.exit(1)
	num_items=len(items)
	return num_items

def print_html_line_graphs(lines):
	for line_name in lines:
		line=lines[line_name]
		if len(line["graphs"]) == 0 or len(line["node_lists"]) == 0:
			continue
		print("""
		<TABLE BORDER>
		<TR>    
				<TH COLSPAN=5>Профиль линии "%(line_name)s"</TH>
		</TR>
		<TR>
				<TH COLSPAN=3>Полная географическая длина линии (метры): %(line_dist).2f</TH>
				<TH COLSPAN=2>Полная длина линии (с учётом высот оснований опор) (метры): %(line_diag_dist).2f</TH>
		</TR>
			</TABLE>

		""" % {"line_name":line_name,"line_dist":line["sum_dist"],"line_diag_dist":line["sum_diag_dist"]})
		
		for way_id in line["ways"]:
			# Пропускаем линии, в которых нет пролётов (например из двух точек, одна из которых не имеет 'ref')
			if not way_id in line["prolet_lists"]:
				continue
			graph_file=line["graphs"][way_id]
			print("""
			<TABLE BORDER>
			<TR>    
					<TH COLSPAN=5>Участок линии с id=%(way_id)d, опоры с %(nach_opora)s по %(konechnaya_opora)s</TH>
			</TR>""" % {"way_id":way_id,"nach_opora":line["node_lists"][way_id][0]["tags"]["ref"],"konechnaya_opora":line["node_lists"][way_id][-1]["tags"]["ref"]})
			print("""<TR>
						<TH COLSPAN=3>Полная географическая длина участка линии (метры): %(line_dist).2f</TH>
						<TH COLSPAN=2>Полная длина участка линии (с учётом высот оснований опор) (метры): %(line_diag_dist).2f</TH>
					</TR>""" % {"line_dist":line["prolet_lists"][way_id]["sum_dist"],"line_diag_dist":line["prolet_lists"][way_id]["sum_diag_dist"]})
			print("</TABLE>")
			print("""<a title="Профиль линии '%(line_name)s'" href="%(graph_file)s"><img src="%(graph_file)s" width="%(width)d" height="%(height)d" border="0"></a>""" \
			% {"line_name":line_name, "graph_file":graph_file, "width":config.graph_x_on_page, "height":config.graph_y_on_page})

	

def print_html_line_profile(lines):
	for line_name in lines:
		line=lines[line_name]
		if len(line["ways"]) == 0 or len(line["node_lists"]) == 0:
			continue
		print("""
		<TABLE BORDER>
		<TR>    
				<TH COLSPAN=5>Профиль линии "%(line_name)s"</TH>
		</TR>
		<TR>
				<TH COLSPAN=3>Полная географическая длина линии (метры): %(line_dist).2f</TH>
				<TH COLSPAN=2>Полная длина линии (с учётом высот оснований опор) (метры): %(line_diag_dist).2f</TH>
		</TR>
		<TR>
		<TH>Пролёт (номер первой и второй опоры)</TH>
		<TH>Длина пролёта географическая (метры)</TH>
		<TH>Расстояние между опорами по диагонали (с учётом разности высот оснований опор) (метры)</TH>
		<TH>Высота над уровнем моря основания первой опоры пролёта (метры)</TH>
		<TH>Высота над уровнем моря основания второй опоры пролёта (метры)</TH>
		</TR>


		""" % {"line_name":line_name,"line_dist":line["sum_dist"],"line_diag_dist":line["sum_diag_dist"]})
		
		for way_id in line["ways"]:
			# Пропускаем линии, в которых нет пролётов (например из двух точек, одна из которых не имеет 'ref')
			if not way_id in line["prolet_lists"]:
				continue
			prolet_list=line["prolet_lists"][way_id]["prolet_list"]
			print("""<TR>    
					<TH COLSPAN=5>Участок линии с id=%(way_id)d, опоры с %(nach_opora)s по %(konechnaya_opora)s</TH>
			</TR>""" % {"way_id":way_id,"nach_opora":line["node_lists"][way_id][0]["tags"]["ref"],"konechnaya_opora":line["node_lists"][way_id][-1]["tags"]["ref"]})
			print("""<TR>
						<TH COLSPAN=3>Полная географическая длина участка линии (метры): %(line_dist).2f</TH>
						<TH COLSPAN=2>Полная длина участка линии (с учётом высот оснований опор) (метры): %(line_diag_dist).2f</TH>
					</TR>""" % {"line_dist":line["prolet_lists"][way_id]["sum_dist"],"line_diag_dist":line["prolet_lists"][way_id]["sum_diag_dist"]})

			for prolet in prolet_list:
				global node_id_to_find
				# Устанавливаем css отрисовки элементов списка:
				if prolet["node1"]["node_id"] == node_id_to_find:
					node1_ref_css="selected_node"
				else:
					node1_ref_css="normaltext"
				if prolet["node2"]["node_id"] == node_id_to_find:
					node2_ref_css="selected_node"
				else:
					node2_ref_css="normaltext"
				if prolet["node1"]["ele"] == 0:
					node1_ele_css="ele_null"
				else:
					node1_ele_css="normaltext"
				if prolet["node2"]["ele"] == 0:
					node2_ele_css="ele_null"
				else:
					node2_ele_css="normaltext"

				print("""<TR>
					 <TD><span class="%(node1_ref_css)s">%(node1_ref)s</span> - <span class="%(node2_ref_css)s">%(node2_ref)s</span></TD>
					 <TD>%(dist).2f</TD>
					 <TD>%(diag_dist).2f</TD>
					 <TD><span class="%(node1_ele_css)s">%(node1_ele).1f</span></TD>
					 <TD><span class="%(node2_ele_css)s">%(node2_ele).1f</span></TD>
					 </TR>""" % \
					 {"node1_ref_css":node1_ref_css, \
					 "node2_ref_css":node2_ref_css, \
					 "node1_ele_css":node1_ele_css, \
					 "node2_ele_css":node2_ele_css, \
					 "node1_ref":prolet["node1"]["tags"]["ref"], \
					 "node2_ref":prolet["node2"]["tags"]["ref"], \
					 "dist":prolet["dist"], \
					 "diag_dist":prolet["diag_dist"], \
					 "node1_ele":prolet["node1"]["ele"], \
					 "node2_ele":prolet["node2"]["ele"] } )

		print("</TABLE>")

def generate_gnuplot_graph(lines):
	for line_name in lines:
		line=lines[line_name]
		line["graphs"]={}
		if len(line["ways"]) == 0 or len(line["node_lists"]) == 0:
			continue

		for way_id in line["ways"]:
			# Пропускаем линии, в которых нет пролётов (например из двух точек, одна из которых не имеет 'ref')
			if not way_id in line["prolet_lists"]:
				continue

			if config.debug:
				line_data_file= config.graph_path+"/line-%d.txt"%way_id
				line_gnuplot_cmd_file=config.graph_path+"/line-%d.plt"%way_id
				line_result_png_file=config.graph_path+"/line-%d.png"%way_id
			else:
				line_data_file=tempfile.mkstemp(suffix=".txt",prefix="gnuplot-%d-"%way_id,dir=config.graph_path)[1]
				line_gnuplot_cmd_file=tempfile.mkstemp(suffix=".plt",prefix="gnuplot-%d-"%way_id,dir=config.graph_path)[1]
				line_result_png_file=tempfile.mkstemp(suffix=".png",prefix="gnuplot-%d-"%way_id,dir=config.graph_path)[1]

			data_file=open(line_data_file,"w+")
			cmd_file=open(line_gnuplot_cmd_file,"w+")

			prolet_list=line["prolet_lists"][way_id]["prolet_list"]
			graph_x=1024
			graph_y=600
			if len(prolet_list) > 20:
				graph_x=len(prolet_list)*50
				
			cmd_file.write("""set terminal  png size %(graph_x)d,%(graph_y)d
set output '%(output_file)s'
set xlabel "Пролёты (м)"
set ylabel "Высота оснований опор над уровнем моря (м)"
set key top left
""" % {"graph_x":graph_x, "graph_y":graph_y, "output_file":line_result_png_file})

			x=0
			for prolet in prolet_list:
				if x==0:
					data_file.write(""""%(ref)s"	%(x)f	%(ele)f\n""" % {"ref":prolet["node1"]["tags"]["ref"], "x":x, "ele":prolet["node1"]["ele"]})
					cmd_file.write("""set label "%(ref)s" at %(x)f,%(ele)f\n""" % {"ref":re.sub(r'["]',r'',prolet["node1"]["tags"]["ref"]), "x":x, "ele":prolet["node1"]["ele"]})
				x+=prolet["dist"]
				data_file.write(""""%(ref)s"	%(x)f	%(ele)f\n""" % {"ref":prolet["node2"]["tags"]["ref"], "x":x, "ele":prolet["node2"]["ele"]})
				cmd_file.write("""set label "%(ref)s" at %(x)f,%(ele)f\n""" % {"ref":re.sub(r'["]',r'',prolet["node2"]["tags"]["ref"]), "x":x, "ele":prolet["node2"]["ele"]})
			# Подписи по оси X:
			cmd_file.write("""
 set xtics (""")
			x=0
			for prolet in prolet_list:
				if x==0:
					cmd_file.write(""""0" 0,""" )
				x+=prolet["dist"]
				cmd_file.write(""""%(prolet).0f" %(x)f""" % {"prolet":prolet["dist"], "x":x})
				# В самом конце списка запятую не ставим:
				if prolet != prolet_list[-1]:
					cmd_file.write(", ")

			cmd_file.write(")\n")

			cmd_file.write("""
set grid
plot '%(line_data_file)s'using 2:3 with linespoints lw 1 lt rgb 'purple' title 'Профиль линии "%(line_name)s"'
		""" % {"line_data_file":line_data_file, "line_name":line_name})
			data_file.close()
			cmd_file.close()
			if config.debug:
				print('/usr/bin/gnuplot {0} &> /dev/null'.format(line_gnuplot_cmd_file))
			os.system('/usr/bin/gnuplot "{0}" &> /dev/null'.format(line_gnuplot_cmd_file))

			line["graphs"][way_id]=config.graph_path+"/"+line_result_png_file.split(os.sep)[-1]


def print_text_line_profile(lines):
	for line_name in lines:
		line=lines[line_name]
		if len(line["ways"]) == 0 or len(line["node_lists"]) == 0:
			continue
		#print("line['ways'] =" , line["ways"])
		#print("line['node_lists'] =" , line["node_lists"])
		print("======= %s =========" % line_name)
		for way_id in line["ways"]:
			# Пропускаем линии, в которых нет пролётов (например из двух точек, одна из которых не имеет 'ref')
			if not way_id in line["prolet_lists"]:
				continue
			print("======= (way_id=%d)=========" % way_id)
			prolet_list=line["prolet_lists"][way_id]["prolet_list"]
			for prolet in prolet_list:
				print("Пролёт между опорами '%s' и '%s'" % (prolet["node1"]["tags"]["ref"], prolet["node2"]["tags"]["ref"] ))
				print("Высота над уровнем моря основания опоры %s - %.1f метров" % (prolet["node1"]["tags"]["ref"], prolet["node1"]["ele"] ))
				print("Высота над уровнем моря основания опоры %s - %.1f метров" % (prolet["node2"]["tags"]["ref"], prolet["node2"]["ele"] ))
				print("географическая длинна пролёта между опорами: %f метров" % prolet["dist"])
				print("расстояние между опорами по диагонали (с учётом разности высот оснований опор): %.2f метров" % prolet["diag_dist"])
				print("Координаты опоры %(ref)s  lat: %(lat)f, lon: %(lon)f" % {"ref":prolet["node1"]["tags"]["ref"], "lat":prolet["node1"]["lat"], "lon":prolet["node1"]["lon"]})
				print("Координаты опоры %(ref)s  lat: %(lat)f, lon: %(lon)f" % {"ref":prolet["node2"]["tags"]["ref"], "lat":prolet["node2"]["lat"], "lon":prolet["node2"]["lon"]})



def print_node(node):
	print ("========= print_node() ========================")
	print("node_id = %d" % node["node_id"])
	print("lat = %f" % node["lat"])
	print("lon = %f" % node["lon"])
	print("ele = %f" % node["ele"])
	print("tags:")
	for k in node["tags"]:
		print("%s = %s" % (k,node["tags"][k]))

def generate_node_list(line):
	global way_id_sql
	global node_id_sql
	line_name=line["line_name"]
	line["node_lists"]={}
	if config.debug:
		print("way_id_sql="+way_id_sql)
	for way_id in line["ways"]:
		node_list=[]
		if config.debug:
			print("line['ways'] =",line["ways"])
			print("way_id =",way_id)
		#print(line_name)
		# Берём список идентификаторов точек в переданной линии, отсортированных по последовательности:
		if config.debug:
			print("""select node_id from way_nodes where way_id=%(way_id)d and (cast(node_id as text) || '-' || cast(version as text) ) in (select (cast(node_id as text) || '-' || cast(max(version) as text) ) as tt from way_nodes where way_id=%(way_id)d group by node_id) order by sequence_id;""" % { "way_id":way_id })
		cur.execute("""select node_id from way_nodes where way_id=%(way_id)d and (cast(way_id as text) || '-' || cast(version as text) ) in (select (cast(way_id as text) || '-' || cast(max(version) as text) ) as tt from way_nodes where way_id=%(way_id)d group by way_id) order by sequence_id;""" % { "way_id":way_id })
		rows = cur.fetchall()
		for row in rows:
			node={}
			node["node_id"]=row[0]
			# Заполняем данные по опорам:
			#cur.execute("""select latitude,longitude from nodes where %(node_id_sql)s=%(node_id)d""" % {"node_id_sql":node_id_sql,"node_id":row[0]})
			if config.debug:
				print("""select %(node_id_sql)s,max(version),latitude,longitude from nodes where %(node_id_sql)s=%(node_id)d and visible='t' group by %(node_id_sql)s,latitude,longitude""" % {"node_id_sql":node_id_sql,"node_id":row[0]})
			cur.execute("""select %(node_id_sql)s,max(version),latitude,longitude from nodes where %(node_id_sql)s=%(node_id)d and visible='t' group by %(node_id_sql)s,latitude,longitude""" % {"node_id_sql":node_id_sql,"node_id":row[0]})
			result =  cur.fetchone()
			node["lat"]=float(result[2])/10**7
			node["lon"]=float(result[3])/10**7

			# Берём теги:
			cur.execute("""select k,v from node_tags where %(node_id_sql)s=%(node_id)d""" % {"node_id_sql":node_id_sql,"node_id":row[0]})
			result = cur.fetchall()
			tags={}
			for tag in result:
				tags[tag[0]]=tag[1]
				if tag[0] == "ele":
					try:
						node["ele"]=float(tag[1])
					except Exception:
						node["ele"]=0
			# Пустая точка без обозначений, либо точка, связывающая с подстанцией "для красоты" - не учитываем её:
			if not "ref" in tags:
				continue
			# Бывает не указана высота:
			if not "ele" in node:
				node["ele"]=0
			node["tags"]=tags
			node_list.append(node)
			#print_node(node)
		if len(node_list) > 1:
		#if node_list.length > 1:
			line["node_lists"][way_id]=node_list


def generate_line_profile(line):
	line_name=line["line_name"]
	line["sum_dist"]=0
	line["sum_diag_dist"]=0
	line["prolet_lists"]={}
	for way_id in line["node_lists"]:
		prolet_list=[]
		prolet_list_data={}
		prolet_list_data["sum_dist"]=0
		prolet_list_data["sum_diag_dist"]=0
		node1={}
		node2={}
		for node in line["node_lists"][way_id]:
			if node1 == {}:
				node1=node
				continue
			node2=node	
			prolet={}
			prolet["node1"]=node1
			prolet["node2"]=node2
			try:
				if config.debug:
					print("Расчёт расстояний между опорами: ref=%(ref1)s (node_id=%(node_id1)s) и ref=%(ref2)s (node_id2=%(node_id2)s) в линии '%(line_name)s':" % {"ref1":node1["tags"]["ref"], "ref2":node2["tags"]["ref"], "line_name":line_name, "node_id1":node1["node_id"], "node_id2":node2["node_id"]})
					print("great_circles(",node1["lon"], node1["lat"],node2["lon"], node2["lat"],")")
					print("great_circles return %f" % great_circles.get_dist(node1["lon"], node1["lat"],node2["lon"], node2["lat"]	))
				prolet["dist"]=great_circles.get_dist(\
					node1["lon"], node1["lat"],\
					node2["lon"], node2["lat"]\
					)
				prolet["diag_dist"]=math.sqrt(math.pow(node1["ele"]-node2["ele"],2)+math.pow(prolet["dist"],2))
				line["sum_dist"]+=prolet["dist"]
				line["sum_diag_dist"]+=prolet["diag_dist"]
				prolet_list_data["sum_dist"]+=prolet["dist"]
				prolet_list_data["sum_diag_dist"]+=prolet["diag_dist"]
			except:	
				print("""Ошибка расчёта расстояний между опорами (скорее всего это ошибка данных на карте. Необходимо сообщить эти данные инженеру, ответственному за наполнение карты):
<br> %(ref1)s (node_id=%(node_id1)d) и %(ref2)s (node_id=%(node_id2)d)в линии '%(line_name)s (way_id=%(way_id)s)'
<br> Ссылка на объект, при обработке которого возникла ошибка: %(url)s
""" % {"node_id1":node1["node_id"],"node_id2":node2["node_id"],"ref1":node1["tags"]["ref"], "ref2":node2["tags"]["ref"], "line_name":line_name,"way_id":way_id,"url":"<a target=\"_self\"  href=\"http://map.prim.drsk.ru/#map=18/%(lat)f/%(lon)f&layer=MFxzlkj&poi=La2\">ссылка на опору с ошибкой</a></BODY>" % {"lat":node1["lat"],"lon":node1["lon"]}});sys.exit()

			prolet_list.append(prolet)
			node1=node2
		prolet_list_data["prolet_list"]=prolet_list
		line["prolet_lists"][way_id]=prolet_list_data



# ======================================= main() ===========================

try:
	if config.debug:
		print("connect to: dbname='" + config.db_name + "' user='" +config.db_user + "' host='" + config.db_host + "' password='" + config.db_passwd + "'")
	conn = psycopg2.connect("dbname='" + config.db_name + "' user='" +config.db_user + "' host='" + config.db_host + "' password='" + config.db_passwd + "'")
	cur = conn.cursor()
except:
    print ("I am unable to connect to the database");sys.exit(1)

num_towers = get_num_of_tower()

num_lines_as_ways = get_num_of_lines_as_ways()
num_lines_as_relation = get_num_of_lines_as_relations()

num_tp_as_node = get_num_of_tp_as_node()
num_tp_as_ways = get_num_of_tp_as_ways()
num_tp_as_relation = get_num_of_tp_as_relations()

num_station_as_node = get_num_of_station_as_node()
num_station_as_ways = get_num_of_station_as_ways()
num_station_as_relation = get_num_of_station_as_relations()

num_all_tp=num_tp_as_node+num_tp_as_ways+num_tp_as_relation
num_all_lines=num_lines_as_ways+num_lines_as_relation
num_all_stations=num_station_as_node+num_station_as_ways+num_station_as_relation


print("num_towers=%d" % num_towers)
print("num_lines_as_ways=%d" % num_lines_as_ways)
print("num_lines_as_relation=%d" % num_lines_as_relation)
print("num_tp_as_node=%d" % num_tp_as_node)
print("num_tp_as_ways=%d" % num_tp_as_ways)
print("num_tp_as_relation=%d" % num_tp_as_relation)
print("num_station_as_node=%d" % num_station_as_node)
print("num_station_as_ways=%d" % num_station_as_ways)
print("num_station_as_relation=%d" % num_station_as_relation)
