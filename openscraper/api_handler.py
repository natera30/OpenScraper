# -*- encoding: utf-8 -*-

import 	pprint
from 	pprint import pprint, pformat

import 	json
from 	bson import json_util, ObjectId
from 	boltons.iterutils import remap

from 	base_handler import *
from 	base_utils	import *



### TO DO 


### + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + ###
### API handlers as background tasks ########################################################
### + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + ###

class APIrestHandler(BaseHandler): 
	"""
	list all contributors from db.contributors
	"""
	@print_separate(APP_DEBUG)
	# @tornado.web.authenticated
	# @check_user_permissions
	# @tornado.web.asynchronous
	# @gen.coroutine
	# @onthread
	def get(self, slug=None):

		print 
		app_log.info("••• APIrestHandler.get ...\n")

		self.site_section = "api"

		# get current page 
		current_page = self.get_current_uri_without_error_slug()
		app_log.info("••• APIrestHandler.get / current_page : %s", current_page )

		# get slug
		slug_ = self.request.arguments
		app_log.info("••• APIrestHandler.get / slug_ : \n %s", pformat(slug_) )

		# filter slug
		query_data = self.filter_slug( slug_, slug_class="data", query_from="api" )
		app_log.info("••• APIrestHandler.get / query_data : \n %s ", pformat(query_data) )

		### check user auth level 
		# --> open data level : "opendata", "commons", "collective", "admin"
		# check OPEN_LEVEL_DICT in settings_corefields.py for more infos
		open_level = "opendata"
		token = query_data["token"]
		if token != None : 
			# TO DO : check token to get corresponding opendata level 
			open_level = "commons"
			
			# log query as warning if request allowed get private or collective info
		
		# TO DO : limit results 
		# override 
		if open_level == "opendata" and query_data["results_per_page"] > QUERIES_MAX_RESULTS_IF_API :
			query_data["results_per_page"] = QUERIES_MAX_RESULTS_IF_API
				
		### retrieve datamodel from DB top make correspondances field's _id --> field_name
		data_model_custom_cursor	= self.application.coll_model.find({"field_class" : "custom", "is_visible" : True }) 
		data_model_custom 			= list(data_model_custom_cursor)
		data_model_dict 			= { str(field["_id"]) : field for field in data_model_custom }

		data_model_core_cursor 		= self.application.coll_model.find({"field_class" : "core" }) 
		data_model_core 			= list(data_model_core_cursor)
		
		app_log.info("••• APIrestHandler.get / data_model_dict : \n %s", pformat(data_model_dict) )
		app_log.info("••• APIrestHandler.get / data_model_custom[:1] : \n %s", pformat(data_model_custom[:1]) )
		app_log.info("••• APIrestHandler.get / data_model_core[:1]   : \n %s", pformat(data_model_core[:]) )
		print "..."

		### filter results depending on field's opendata level
		# get fields allowed
		# open_level 				= query_data[open_level]
		# allowed_open_levels 	= OPEN_LEVEL_DICT[open_level]
		# allowed_custom_fields	= [ unicode(str(dm["_id"])) for dm in data_model_custom if dm["field_open"] in allowed_open_levels ]
		# app_log.info("••• APIrestHandler.get / allowed_custom_fields : %s", allowed_custom_fields )

		allowed_fields = self.get_authorized_datamodel_fields(open_level, data_model_custom, data_model_core )
		
		# get data 
		data, is_data, page_n_max = self.get_data_from_query( 	query_data, 
																coll_name			= "data", 
																query_from			= self.site_section, 
																keep_fields_list	= allowed_fields,
																ignore_fields_list	= ["_id"]
															)
		# data, is_data, page_n_max = raw[0], raw[1], raw[3]
		app_log.info("••• APIrestHandler.get / is_data : %s ", is_data ) 

		
		
		### operations if there is data
		if is_data : 
			
			count_results = len(data)
			app_log.info("••• APIrestHandler.get / data[0] : \n %s " , pformat(data[0]) )
			
			### rewrite field names as understable ones --> replace field_oid by field_name 
			# cf : https://sedimental.org/remap.html
			data = remap( data, lambda p, k, v: ( data_model_dict[k][u"field_name"], v) if k in data_model_dict else (k, v))

			# ### write data as json
			# # cf : https://stackoverflow.com/questions/35083374/how-to-decode-a-unicode-string-python
			# # self.write(json.dumps(data, default=json_util.default)) 
			# self.write(json.dumps(data, ensure_ascii=False, default=json_util.default).encode('utf8') )

			# print '.....\n' 
	
		else :
			count_results = 0
			data = "no data for this query"

			# self.write("no data for this query") 
			# print '.....\n' 

		### add header to tell user which level auth he/she gets to get
		full_json = { 
			
			"header" : {
				"auth_level" 	: open_level ,
				"query"			: query_data ,
				"query_uri"		: self.request.uri ,
				"count_results"	: count_results
			},
			
			"data_list" 	 	: data
		}

		### write data as json
		# cf : https://stackoverflow.com/questions/35083374/how-to-decode-a-unicode-string-python
		results = json.dumps(full_json, ensure_ascii=False, default=json_util.default).encode('utf8')

		print '.....\n' 

		# self.write( results )
		self.write( results )
		# raise gen.Return(self.write( results ))