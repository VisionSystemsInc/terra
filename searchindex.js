Search.setIndex({docnames:["index","python/modules","python/terra","python/terra.compute","python/terra.core","python/terra.executor","python/terra.executor.celery","python/terra.utils","terra/apps","terra/contributing","terra/getting_started","terra/settings"],envversion:{"sphinx.domains.c":1,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":1,"sphinx.domains.javascript":1,"sphinx.domains.math":2,"sphinx.domains.python":1,"sphinx.domains.rst":1,"sphinx.domains.std":1,"sphinx.ext.intersphinx":1,"sphinx.ext.todo":2,sphinx:56},filenames:["index.rst","python/modules.rst","python/terra.rst","python/terra.compute.rst","python/terra.core.rst","python/terra.executor.rst","python/terra.executor.celery.rst","python/terra.utils.rst","terra/apps.rst","terra/contributing.rst","terra/getting_started.rst","terra/settings.rst"],objects:{"":{TERRA_SETTINGS_FILE:[4,7,1,"-"],TERRA_UNITTEST:[2,7,1,"-"],service_end:[11,8,1,"cmdoption-arg-service-end"],service_start:[11,8,1,"cmdoption-arg-service-start"],terra:[2,0,0,"-"]},"terra.compute":{base:[3,0,0,"-"],container:[3,0,0,"-"],docker:[3,0,0,"-"],dummy:[3,0,0,"-"],singularity:[3,0,0,"-"],utils:[3,0,0,"-"],virtualenv:[3,0,0,"-"]},"terra.compute.base":{AlreadyRegisteredException:[3,1,1,""],BaseCompute:[3,2,1,""],BaseService:[3,2,1,""],ServiceRunFailed:[3,1,1,""]},"terra.compute.base.BaseCompute":{configuration_map_service:[3,3,1,""],configure_logger:[3,3,1,""],get_volume_map:[3,3,1,""],reconfigure_logger:[3,3,1,""],register:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.base.BaseService":{_validate_volume:[3,3,1,""],add_volume:[3,3,1,""],post_run:[3,3,1,""],pre_run:[3,3,1,""],volumes:[3,4,1,""]},"terra.compute.container":{ContainerService:[3,2,1,""]},"terra.compute.container.ContainerService":{add_volume:[3,3,1,""],post_run:[3,3,1,""],pre_run:[3,3,1,""]},"terra.compute.docker":{Compute:[3,2,1,""],Service:[3,2,1,""],docker_volume_re:[3,5,1,""]},"terra.compute.docker.Compute":{config_service:[3,3,1,""],configuration_map_service:[3,3,1,""],get_volume_map:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.dummy":{Compute:[3,2,1,""],Service:[3,2,1,""]},"terra.compute.dummy.Compute":{create_service:[3,3,1,""],remove_service:[3,3,1,""],run_service:[3,3,1,""],start_service:[3,3,1,""],stop_service:[3,3,1,""]},"terra.compute.dummy.Service":{post_run:[3,3,1,""],pre_run:[3,3,1,""]},"terra.compute.singularity":{Compute:[3,2,1,""],Service:[3,2,1,""]},"terra.compute.singularity.Compute":{config_service:[3,3,1,""],configuration_map_service:[3,3,1,""],get_volume_map:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.utils":{ComputeHandler:[3,2,1,""],compute:[3,5,1,""],get_default_service_class:[3,6,1,""],just:[3,6,1,""],load_service:[3,6,1,""],translate_settings_paths:[3,6,1,""]},"terra.compute.utils.ComputeHandler":{_connect_backend:[3,3,1,""]},"terra.compute.virtualenv":{Compute:[3,2,1,""],Service:[3,2,1,""]},"terra.compute.virtualenv.Compute":{add_volume:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.virtualenv.Service":{post_run:[3,3,1,""],pre_run:[3,3,1,""]},"terra.core":{exceptions:[4,0,0,"-"],settings:[4,0,0,"-"],signals:[4,0,0,"-"],utils:[4,0,0,"-"]},"terra.core.exceptions":{ConfigurationWarning:[4,1,1,""],ImproperlyConfigured:[4,1,1,""]},"terra.core.settings":{ENVIRONMENT_VARIABLE:[4,5,1,""],ExpandedString:[4,2,1,""],LazyObject:[4,2,1,""],LazySettings:[4,2,1,""],LazySettingsThreaded:[4,2,1,""],ObjectDict:[4,2,1,""],Settings:[4,2,1,""],TerraJSONEncoder:[4,2,1,""],filename_suffixes:[4,5,1,""],global_templates:[4,5,1,""],json_include_suffixes:[4,5,1,""],need_to_set_virtualenv_dir:[4,6,1,""],processing_dir:[4,6,1,""],settings:[4,5,1,""],settings_property:[4,6,1,""],status_file:[4,6,1,""],terra_uuid:[4,6,1,""],unittest:[4,6,1,""]},"terra.core.settings.LazyObject":{__contains__:[4,3,1,""],__delattr__:[4,3,1,""],__delitem__:[4,3,1,""],__dir__:[4,3,1,""],__getattr__:[4,3,1,""],__getitem__:[4,3,1,""],__iter__:[4,3,1,""],__len__:[4,3,1,""],__setattr__:[4,3,1,""],__setitem__:[4,3,1,""],_setup:[4,3,1,""]},"terra.core.settings.LazySettings":{_setup:[4,3,1,""],add_templates:[4,3,1,""],configure:[4,3,1,""],configured:[4,3,1,""]},"terra.core.settings.LazySettingsThreaded":{__setattr__:[4,3,1,""],downcast:[4,3,1,""]},"terra.core.settings.ObjectDict":{__dir__:[4,3,1,""],__getattr__:[4,3,1,""],__setattr__:[4,3,1,""],update:[4,3,1,""]},"terra.core.settings.Settings":{__getattr__:[4,3,1,""]},"terra.core.settings.TerraJSONEncoder":{"default":[4,3,1,""],dumps:[4,3,1,""],serializableSettings:[4,3,1,""]},"terra.core.signals":{Signal:[4,2,1,""],logger_configure:[4,5,1,""],logger_reconfigure:[4,5,1,""],post_settings_configured:[4,5,1,""],post_settings_context:[4,5,1,""],receiver:[4,6,1,""]},"terra.core.signals.Signal":{_live_receivers:[4,3,1,""],connect:[4,3,1,""],disconnect:[4,3,1,""],has_listeners:[4,3,1,""],receivers:[4,4,1,""],send:[4,3,1,""],send_robust:[4,3,1,""],sender_receivers_cache:[4,4,1,""],use_caching:[4,4,1,""]},"terra.core.utils":{ClassHandler:[4,2,1,""],Handler:[4,2,1,""],cached_property:[4,2,1,""]},"terra.core.utils.ClassHandler":{_connect_backend:[4,3,1,""]},"terra.core.utils.Handler":{_connect_backend:[4,3,1,""],close:[4,3,1,""]},"terra.core.utils.cached_property":{__get__:[4,3,1,""],func:[4,3,1,""],name:[4,4,1,""]},"terra.executor":{base:[5,0,0,"-"],celery:[6,0,0,"-"],dummy:[5,0,0,"-"],process:[5,0,0,"-"],sync:[5,0,0,"-"],thread:[5,0,0,"-"],utils:[5,0,0,"-"]},"terra.executor.base":{BaseExecutor:[5,2,1,""],BaseFuture:[5,2,1,""]},"terra.executor.base.BaseExecutor":{configure_logger:[5,3,1,""],reconfigure_logger:[5,3,1,""]},"terra.executor.celery":{CeleryExecutor:[6,2,1,""],celeryconfig:[6,0,0,"-"],executor:[6,0,0,"-"]},"terra.executor.celery.CeleryExecutor":{configuration_map:[6,3,1,""],configure_logger:[6,3,1,""],reconfigure_logger:[6,3,1,""],shutdown:[6,3,1,""],submit:[6,3,1,""]},"terra.executor.celery.executor":{CeleryExecutor:[6,2,1,""],CeleryExecutorFuture:[6,2,1,""],setup_loggers:[6,6,1,""]},"terra.executor.celery.executor.CeleryExecutor":{configuration_map:[6,3,1,""],configure_logger:[6,3,1,""],reconfigure_logger:[6,3,1,""],shutdown:[6,3,1,""],submit:[6,3,1,""]},"terra.executor.celery.executor.CeleryExecutorFuture":{cancel:[6,3,1,""]},"terra.executor.dummy":{DummyExecutor:[5,2,1,""]},"terra.executor.dummy.DummyExecutor":{shutdown:[5,3,1,""],submit:[5,3,1,""]},"terra.executor.process":{ProcessPoolExecutor:[5,2,1,""]},"terra.executor.sync":{SyncExecutor:[5,2,1,""]},"terra.executor.sync.SyncExecutor":{shutdown:[5,3,1,""],submit:[5,3,1,""]},"terra.executor.thread":{ThreadPoolExecutor:[5,2,1,""]},"terra.executor.utils":{Executor:[5,5,1,""],ExecutorHandler:[5,2,1,""]},"terra.executor.utils.ExecutorHandler":{_connect_backend:[5,3,1,""],configuration_map:[5,3,1,""]},"terra.logger":{DEBUG1:[2,5,1,""],DEBUG2:[2,5,1,""],DEBUG3:[2,5,1,""],DEBUG4:[2,5,1,""],Logger:[2,2,1,""],getLogger:[2,6,1,""]},"terra.logger.Logger":{debug1:[2,3,1,""],debug2:[2,3,1,""],debug3:[2,3,1,""],debug4:[2,3,1,""],fatal:[2,3,1,""],findCaller:[2,3,1,""]},"terra.task":{TerraTask:[2,2,1,""],shared_task:[2,6,1,""]},"terra.task.TerraTask":{apply_async:[2,3,1,""],translate_paths:[2,3,1,""]},"terra.utils":{cli:[7,0,0,"-"],workflow:[7,0,0,"-"]},"terra.utils.cli":{ArgumentParser:[7,2,1,""],DbStopAction:[7,2,1,""],FullPaths:[7,2,1,""],FullPathsAppend:[7,2,1,""],clean_path:[7,6,1,""]},"terra.utils.workflow":{AlreadyRunException:[7,1,1,""],resumable:[7,2,1,""]},"terra.utils.workflow.resumable":{save_status:[7,3,1,""]},"terra.workflow":{BaseWorkflow:[2,2,1,""],PipelineWorkflow:[2,2,1,""]},"terra.workflow.BaseWorkflow":{run:[2,3,1,""]},"terra.workflow.PipelineWorkflow":{run:[2,3,1,""],service_index:[2,3,1,""]},logging:{date_format:[11,8,1,"cmdoption-arg-logging-date-format"],format:[11,8,1,"cmdoption-arg-logging-format"],format_style:[11,8,1,"cmdoption-arg-logging-format-style"],level:[11,8,1,"cmdoption-arg-logging-level"]},terra:{compute:[3,0,0,"-"],core:[4,0,0,"-"],executor:[5,0,0,"-"],logger:[2,0,0,"-"],settings:[2,5,1,""],task:[2,0,0,"-"],utils:[7,0,0,"-"],workflow:[2,0,0,"-"],zone:[11,8,1,"cmdoption-arg-terra-zone"]}},objnames:{"0":["py","module","Python module"],"1":["py","exception","Python exception"],"2":["py","class","Python class"],"3":["py","method","Python method"],"4":["py","attribute","Python attribute"],"5":["py","data","Python data"],"6":["py","function","Python function"],"7":["std","envvar","environment variable"],"8":["std","cmdoption","program option"]},objtypes:{"0":"py:module","1":"py:exception","2":"py:class","3":"py:method","4":"py:attribute","5":"py:data","6":"py:function","7":"std:envvar","8":"std:cmdoption"},terms:{"7f798335ee3b":4,"abstract":4,"case":[2,4,7,11],"catch":4,"class":[2,3,4,5,6,7],"const":7,"default":[2,3,7,10,11],"final":2,"function":[2,3,4,7],"import":[2,3,4,10],"new":[5,9],"null":3,"return":[2,3,4,5,6],"static":[3,4,5,6],"super":3,"throw":4,"transient":4,"true":[3,4,5,6],"try":4,"while":10,Added:2,Adding:0,And:2,For:[3,4,11],Not:7,One:4,The:[2,3,5,7,8,9,10,11],These:[4,7,10],Use:3,Used:[3,4],Using:2,Will:[4,6],__contains__:4,__delattr__:4,__delitem__:4,__dict__:4,__dir__:4,__exit__:4,__get__:4,__getattr__:4,__getitem__:4,__init__:3,__iter__:4,__len__:4,__name__:2,__setattr__:4,__setitem__:4,_appendact:7,_base:5,_connect_backend:[3,4,5],_dir:4,_file:4,_json:4,_live_receiv:4,_override_typ:[3,5],_path:4,_setup:4,_validate_volum:3,abl:4,abov:[2,3],absolut:7,accept:[3,4],access:[2,3,4,10],accomplish:10,accord:2,action:[3,4,7],actual:[3,4],adapt:3,add:[3,8,9],add_templ:4,add_volum:3,added:4,adding:4,addit:4,advanc:10,after:[2,3,4,5,6],again:4,against:4,agnost:[2,10],algorithm:[2,4,10],all:[2,3,4,5,6,10,11],allow:[3,4,5],allow_nan:4,along:4,alreadi:[2,3,4,5,6,7],alreadyregisteredexcept:3,alreadyrunexcept:7,also:[2,3],alter:2,altern:6,altogeth:4,alwai:[2,7],ani:[2,3,4,5,10],anoth:[2,4],anyth:4,anywher:2,api:5,app1:8,app2:8,app:[0,2,3,4,7,10],appear:2,append:2,appli:10,applic:4,apply_async:[2,6],applyasync_kwarg:6,appnam:8,arbitrari:4,arch:[2,3,4,10],architectur:[2,3,10],area:11,arg:[2,3,4,5,6,7],argpars:7,args2:2,argument:[2,3,4,7],argumentpars:7,asctim:[4,11],assign:4,associ:[5,6],asyncresult:6,attempt:[4,5,7],attribut:[4,10,11],automat:[3,4,11],avail:2,back:4,backend:[3,5],bar:4,base:[1,2,4,6,7],basecomput:3,baseexecutor:[5,6],basefutur:[5,6],baseservic:3,baseworkflow:2,basic:2,basicdecor:7,been:[3,4,5,6],befor:[2,3,6],begin:7,behavior:[4,5],being:[2,3,4],best:2,between:6,bool:4,both:4,bypass:4,cach:[3,4],cached_properti:4,call:[2,3,4,5,6],caller:2,can:[2,3,4,5,6,7,9,10,11],cancel:6,cannot:[3,6],captur:2,celeri:[2,5],celeryconfig:[2,5],celeryexecutor:6,celeryexecutorfutur:6,certain:4,chane:3,chang:6,charact:2,check:[4,6],check_circular:4,check_remot:3,children:4,choic:7,choos:11,circumst:[2,4],classhandl:[4,5],classmethod:[3,4],clean:[4,5,6],clean_path:7,cli:[1,2,10,11],close:4,cls:[3,4],code:[2,3],com:[4,5],combin:10,come:5,command:3,compil:4,complet:6,complic:4,componet:4,compos:3,compose_fil:3,compose_service_nam:3,comput:[1,2,4,5,10,11],computehandl:3,concurr:5,condit:3,condition:4,conf:4,config:[3,4],config_servic:3,configur:[2,3,4,10],configuration_map:[5,6],configuration_map_servic:3,configurationwarn:4,configure_logg:[3,5,6],conform:5,connect:[3,4,5],connectionhandl:4,consequ:5,consid:4,consist:3,contain:[1,2,4,10,11],container_config:3,container_platform:3,containerservic:3,content:[0,1],context:4,contribut:0,control:[4,10,11],conveni:4,convert:4,copi:[3,4],core:[1,2,3,5,7,10],correct:3,could:[4,5,11],cours:3,crash:2,creat:[2,3,9],create_servic:3,critic:2,current:[4,5,8],custom:[2,3,4],data:[4,10],date:11,date_format:[4,11],dbstopact:7,debug1:2,debug2:2,debug3:[2,4],debug4:2,debug:[2,4],decor:[4,7],decoupl:4,def:4,default_index:2,default_set:4,defin:[3,4],definit:[3,11],delai:6,deleg:[2,3],depend:11,deploi:[2,10],describ:4,descriptor:4,design:[2,7],dest:7,detail:4,determ:4,develop:2,dict:[3,4,10],dictionari:[4,10],differ:11,directori:[2,3,4,7],disabl:4,disconnect:4,dispatch:4,dispatch_uid:4,displai:2,distinct:4,django:4,djangoproject:4,doc:[4,11],docker:[1,2,8],docker_volume_r:3,document:4,doe:[3,4,5],doesn:4,don:[4,5,11],done:4,down:[2,3],downcast:[4,5],downsid:5,drive:3,dummi:[1,2,4],dummyexecutor:5,dump:4,dure:[2,4],each:[4,5,9],earlier:10,eas:10,easier:3,easili:[2,4],edit:5,effect:5,either:[3,4,5,11],element:4,els:[4,10],elsewher:4,emit:2,empti:3,encod:4,end:11,ensure_ascii:4,entrypoint:[3,5],env:3,environ:[2,3,4,10],environment_vari:4,error:[4,6],especi:4,essenti:4,etc:[2,3,10],evalu:4,even:[2,4],event:4,everi:7,everyth:[2,10],exampl:[4,5,8],except:[1,2,3,7],execut:[3,4,5,6,7,11],executor:[1,2,3,4,11],executor_volume_map:2,executorhandl:5,exist:[2,3],expand:7,expandedstr:4,expect:2,explain:4,expos:4,express:3,extern:8,extra:2,extrem:2,failur:7,fals:[2,3,4,6,7],fashion:4,fatal:2,file:[2,3,4,7,8,10],filenam:4,filename_suffix:4,filter:4,find:2,findcal:2,finish:[5,6],first:[4,10,11],flag:[3,7],folder:3,follow:[2,3],foo:4,format:[4,11],format_styl:11,four:2,frame:2,framework:4,friendli:4,from:[2,3,4,5,10],full:[3,4],fulli:[3,5],fullpath:7,fullpathsappend:7,func:4,futur:[5,6],gener:[2,4],get:[0,3,4],get_absolute_url:4,get_default_service_class:3,get_volume_map:3,getlogg:2,give:[3,5],given:[3,5],global:4,global_set:4,global_templ:[4,10],goal:[2,10],good:7,group:3,guidlin:0,handl:[3,4],handler:[2,3,4,5],happen:[4,5],has:[3,4,5,6,7],has_listen:4,hashabl:4,hasn:4,have:[3,4,5,6,7],help:[4,7],helper:4,here:[4,10],holder:3,home:7,hood:10,host:[3,11],hostnam:4,how:[2,4],howev:[4,5],howto:4,html:[4,11],http:[4,5,11],identifi:4,implement:[3,4,6],improperli:4,improperlyconfigur:4,includ:[4,8,11],inclus:11,inde:4,indent:4,index:[0,10],individu:4,influenc:5,info:4,inform:[3,7,10],infrastructur:[2,10],inherit:3,initarg:5,initi:[2,4,5,11],inject:7,input:[3,10],insensit:11,instanc:[3,4],instanti:4,instead:[3,4,10],intend:5,interact:[3,5],interest:[2,4],interfac:[3,5],intern:[4,5,6],interpret:2,invok:4,isn:4,isol:5,item:4,iter:4,its:[4,5],itself:3,job:5,json:[4,7,10],json_include_suffix:4,jsonencod:4,junk:3,just:[3,4,5],just_temp_arrai:8,justfil:[3,8],keep:5,kei:4,keyword:4,known:5,kwarg:[2,3,4,5,6,7],kwargs2:2,larger:4,last:[3,10,11],later:4,layer:11,lazi:4,lazili:4,lazyobject:4,lazyset:[2,4],lazysettingsthread:[4,5],least:[3,7],left:7,let:4,level:[2,4,11],levelnam:[4,11],librari:11,like:[2,4,11],limit:5,line:[2,3],linux:3,list:[2,3,4,10],live:4,load:[3,4,5],load_servic:3,local:[3,5],local_must_exist:3,log:[0,2,4,5,10],logger:[1,4],logger_configur:4,logger_reconfigur:4,logrecord:11,loop:4,loos:4,loosli:4,magic:4,mai:[2,4],main:[8,10,11],mainli:[3,5],make:[4,7],mani:4,manual:4,map:[3,4],master:11,match:10,math:2,matter:3,max_tim:4,max_work:[5,6],messag:[2,3,4,5,11],metadata:4,metavar:7,method:[4,5,6],might:[3,4],mock:4,mock_foo:4,model:3,modul:[0,1],more:[2,4,7],most:[2,3],mostli:4,mount:3,mp_context:5,msg:2,multipl:[2,5,7,10],must:[4,7],my_set:10,mymodel:4,name:[2,3,4,5,7],name_or_class:3,narg:7,necessari:[2,4],need:[2,3,4],need_to_set_virtualenv_dir:4,nest:[4,10],nested_upd:10,new_cal:4,newli:2,no_remot:3,nocopi:3,non:[3,4,7],none:[2,3,4,5,6,7,11],normal:[4,5],notat:11,note:[2,4,5],noth:5,notifi:4,notimplementederror:4,now:2,number:[2,11],nutshel:4,obj:4,object:[2,3,4,5,7],objectdict:4,occur:[2,4],off:[3,4,5,7],old:3,onc:[2,4,7,10],one:[2,4,5,6,7,10,11],ones:10,onli:[2,4,5,7,11],oper:4,option:[3,4,5,6,9,11],option_str:7,order:[8,10],org:[4,11],origin:[2,4],other:[3,4,5,6,11],otherwis:[4,5,6],out:4,output:[2,3,10,11],overload:4,overrid:[3,4,5,10],overridden:3,override_typ:[3,4,5],own:5,packag:[0,1],page:0,pair:[3,4,10],parallel:5,param:4,paramet:[3,4,5,6],pars:[3,4],part:[2,3],partial:[3,5],particular:[3,4],pass:[3,4,6],patch:4,path:[3,7],pattern:[4,10],payload:2,pick:7,piec:[4,7],pipelin:[2,11],pipelineworkflow:[2,11],place:[3,4],plugin:8,point:4,popen:3,popul:4,port:4,possibl:[4,6],post_:3,post_delet:4,post_run:3,post_sav:4,post_settings_configur:4,post_settings_context:[4,6],postdelai:6,potenti:5,pre_:3,pre_run:3,pre_run_task:6,predelai:6,prefix:[2,3],prepend:3,prepopul:10,prevent:4,primarili:3,print:[3,4],prior:4,privat:3,process:[1,2,3,4],processing_dir:[2,4],processnam:4,processpoolexecutor:[4,5],programat:3,propag:4,properti:4,propertymock:4,providing_arg:4,proxi:4,purpos:[2,10],put:4,python:[2,7,10,11],qualifi:[3,5],queue:6,quintessenti:3,rais:[3,4,7],random:2,rare:[2,4],rather:[4,5],read:[7,11],realli:2,receiv:4,reclaim:[5,6],recommend:4,reconfigur:4,reconfigure_logg:[3,5,6],recurs:4,redefin:4,refer:[4,9],referenc:4,regist:[3,4],regular:3,rel:7,remain:4,remot:3,remov:[2,4],remove_servic:3,repetit:2,replac:4,replai:2,repo:8,report:5,repres:[4,10],requir:7,resolv:[4,5],resourc:[5,6],respond:4,respons:[3,4],result:[4,5],resum:[4,7],retri:6,retriev:4,retry_kwarg:6,retry_queu:6,return_valu:4,reverse_compute_volume_map:2,rogu:5,role:9,root:2,rst:9,run:[2,3,4,5,6,7,10,11],run_servic:3,runner:[3,5,11],runtim:2,safe:[4,5,6,7],same:[2,3,4,10],save:2,save_statu:7,scenario:5,scope:4,screen:2,search:0,second:[2,4,7,10],see:[2,3,4],seen:2,self:[2,3,4,5,7],send:4,send_robust:4,sender:[3,4,5,6],sender_receivers_cach:4,sensibl:4,sent:[3,4],separ:[3,4],sequenc:4,serial:[2,4],serializ:4,serializableset:4,server:4,servic:[2,3,5,11],service_end:11,service_index:2,service_info:[3,5,6],service_nam:2,service_start:11,servicerunfail:3,set:[0,1,2,3,5,6,7,8,9],set_temp_arrai:8,setting_nam:9,settings_properti:4,setup:[2,10],setup_logg:6,sever:[5,6],share:3,shared_task:2,should:[2,3,4,8,9,10,11],shouldn:4,show:8,shutdown:[5,6],side:5,signal:[1,2],signal_receiv:4,signals_receiv:4,similar:4,simpl:[2,4],simpli:[7,10],simplier:4,sinc:[3,4],singl:[3,4,5],singular:[1,2],situat:7,skip:[7,11],skipkei:4,slave:3,snippet:5,some:[4,11],somehow:4,someth:[4,10],sort_kei:4,sourc:[2,3],spam:2,special:6,specif:[2,3,4],specifi:[2,3,4],src1:8,src2:8,stack:2,stack_info:2,stacklevel:2,stackoverflow:5,stage:[7,11],standard:3,start:[0,3,5,11],start_servic:3,state:6,statement:[2,4],statu:[4,7],status_fil:[4,7],stdout:2,step:3,stop_servic:3,storag:5,store:4,str:[3,4,5],string:[3,4,11],strong:4,structur:[4,5,10],stuff:4,style:[3,4,11],subclass:4,submit:[5,6],submodul:[1,8],subpackag:1,subsequ:4,subset:4,suffix:4,sugar:6,support:4,sync:[1,2],syncexecutor:5,synchron:5,system:2,taken:4,target:3,task:[1,5,6,8,11],task_id:2,tell:4,templat:[4,10],temporari:[2,4],termin:4,terra:[8,9],terra_app1_cwd:8,terra_app1_dir:8,terra_app1_dir_dock:8,terra_app2_cwd:8,terra_app2_dir:8,terra_app2_dir_dock:8,terra_celery_includ:8,terra_celery_main_nam:8,terra_initial_tmp_xxxxxxxx:2,terra_log:2,terra_pythonpath:8,terra_settings_fil:[2,10],terra_terra_volum:8,terra_unittest:[2,4],terra_uuid:4,terrajsonencod:4,terratask:2,test:[2,5],than:[3,4,5,7],thei:[2,3,4],them:[4,9],thi:[2,3,4,5,6,7,8,10,11],though:4,thread:[1,2],threadpoolexecutor:5,three:[2,11],through:4,thrown:[3,7],time:[2,3,4,5,6,7],todo:10,tool:[7,10],topic:4,track:7,translat:[3,4],translate_path:2,translate_settings_path:3,treat:5,trigger:[4,6],trivial:4,tupl:[3,4,10],turn:[4,7],two:[2,3],type:[2,3,4,5,7],typeerror:4,typic:[5,8],under:[3,4],underli:2,underneath:10,unevalu:[2,4],unexpect:4,uninstanti:4,unintend:5,uniqu:4,unit:2,unittest:4,unless:4,unlik:5,unset:4,unspecifi:4,until:[4,5,6],updat:[4,7,11],update_delai:6,url:4,usag:[1,10],use:[2,4,5,10],use_cach:4,used:[2,3,4,5,6,7,8,9,10],useful:[2,4],user:[2,4,7],uses:4,using:[3,4,6,7,10,11],usual:[3,4,10],util:[1,2],uuid:4,valid:3,valu:[4,10],valueerror:3,variabl:[2,3,4,10,11],verbos:2,version:5,via:[3,10],virtual:3,virtualenv:[1,2,4],virtualenv_dir:[3,4],volum:[3,4],volume_map:[3,4],vsi:[7,10],vsi_common:8,wai:[2,3,10,11],wait:[5,6],want:[3,4,7,11],warn:[2,4,11],weak:4,weakkeydictionari:4,weakref:4,what:[0,3,5],when:[2,3,4,5,7,9,10],where:[2,4,5,7,10],whether:[2,4],which:[3,4,5,11],whose:3,window:3,within:10,without:2,won:4,work:[4,7],workflow:[0,1,3],would:[2,4,5],wrap:[3,4],wrapper:4,write:[4,7],writeabl:4,you:[3,4,7,11],your:[2,4],zero:3,zone:[4,5,11]},titles:["Welcome to Terra\u2019s documentation!","terra","terra package","terra.compute package","terra.core package","terra.executor package","terra.executor.celery package","terra.utils package","Adding Apps","Contributing Guidlines","What is Terra","Terra Settings"],titleterms:{"default":4,Adding:8,The:4,Using:4,alter:4,app:8,avail:4,base:[3,5],basic:4,celeri:6,celeryconfig:6,cli:7,code:4,comput:3,contain:3,content:[2,3,4,5,6,7],contribut:9,core:4,design:4,docker:3,document:[0,9],dummi:[3,5],except:4,executor:[5,6],get:10,guidlin:9,indic:0,log:11,logger:2,modul:[2,3,4,5,6,7],packag:[2,3,4,5,6,7],process:5,python:4,runtim:4,set:[4,10,11],signal:4,singular:3,start:10,submodul:[2,3,4,5,6,7],subpackag:[2,5],sync:5,tabl:0,task:2,terra:[0,1,2,3,4,5,6,7,10,11],terra_settings_fil:4,thread:5,usag:2,util:[3,4,5,7],virtualenv:3,welcom:0,what:10,without:4,workflow:[2,7,11]}})