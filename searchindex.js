Search.setIndex({docnames:["index","python/modules","python/terra","python/terra.compute","python/terra.core","python/terra.executor","python/terra.executor.celery","python/terra.utils","terra/apps","terra/compute","terra/contributing","terra/executor","terra/getting_started","terra/settings"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":3,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":2,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.intersphinx":1,"sphinx.ext.todo":2,sphinx:56},filenames:["index.rst","python/modules.rst","python/terra.rst","python/terra.compute.rst","python/terra.core.rst","python/terra.executor.rst","python/terra.executor.celery.rst","python/terra.utils.rst","terra/apps.rst","terra/compute.rst","terra/contributing.rst","terra/executor.rst","terra/getting_started.rst","terra/settings.rst"],objects:{"":{TERRA_SETTINGS_FILE:[4,7,1,"-"],TERRA_UNITTEST:[2,7,1,"-"],service_end:[13,8,1,"cmdoption-arg-service_end"],service_start:[13,8,1,"cmdoption-arg-service_start"],terra:[2,0,0,"-"]},"terra.compute":{base:[3,0,0,"-"],container:[3,0,0,"-"],docker:[3,0,0,"-"],dummy:[3,0,0,"-"],singularity:[3,0,0,"-"],utils:[3,0,0,"-"],virtualenv:[3,0,0,"-"]},"terra.compute.base":{AlreadyRegisteredException:[3,1,1,""],BaseCompute:[3,2,1,""],BaseService:[3,2,1,""],ServiceRunFailed:[3,1,1,""]},"terra.compute.base.BaseCompute":{configuration_map_service:[3,3,1,""],configure_logger:[3,3,1,""],get_volume_map:[3,3,1,""],reconfigure_logger:[3,3,1,""],register:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.base.BaseService":{_env_array:[3,3,1,""],_validate_volume:[3,3,1,""],add_volume:[3,3,1,""],post_run:[3,3,1,""],pre_run:[3,3,1,""],volumes:[3,4,1,""]},"terra.compute.container":{ContainerService:[3,2,1,""]},"terra.compute.container.ContainerService":{add_volume:[3,3,1,""],post_run:[3,3,1,""],pre_run:[3,3,1,""]},"terra.compute.docker":{Compute:[3,2,1,""],Service:[3,2,1,""],_docker_volume_flags_re:[3,5,1,""],docker_internal_volume_re:[3,5,1,""],docker_volume_re:[3,5,1,""]},"terra.compute.docker.Compute":{config_service:[3,3,1,""],configuration_map_service:[3,3,1,""],get_volume_map:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.dummy":{Compute:[3,2,1,""],Service:[3,2,1,""]},"terra.compute.dummy.Compute":{create_service:[3,3,1,""],remove_service:[3,3,1,""],run_service:[3,3,1,""],start_service:[3,3,1,""],stop_service:[3,3,1,""]},"terra.compute.dummy.Service":{post_run:[3,3,1,""],pre_run:[3,3,1,""]},"terra.compute.singularity":{Compute:[3,2,1,""],Service:[3,2,1,""]},"terra.compute.singularity.Compute":{config_service:[3,3,1,""],configuration_map_service:[3,3,1,""],get_volume_map:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.utils":{ComputeHandler:[3,2,1,""],compute:[3,5,1,""],get_default_service_class:[3,6,1,""],just:[3,6,1,""],load_service:[3,6,1,""],patch_volume:[3,6,1,""],pathlib_map:[3,6,1,""],translate_settings_paths:[3,6,1,""]},"terra.compute.utils.ComputeHandler":{_connect_backend:[3,3,1,""]},"terra.compute.virtualenv":{Compute:[3,2,1,""],Service:[3,2,1,""]},"terra.compute.virtualenv.Compute":{add_volume:[3,3,1,""],run_service:[3,3,1,""]},"terra.compute.virtualenv.Service":{post_run:[3,3,1,""],pre_run:[3,3,1,""]},"terra.core":{exceptions:[4,0,0,"-"],settings:[4,0,0,"-"],signals:[4,0,0,"-"],utils:[4,0,0,"-"]},"terra.core.exceptions":{ConfigurationWarning:[4,1,1,""],ImproperlyConfigured:[4,1,1,""],NO_STACK_EXCEPTIONS:[4,5,1,""],NoStackException:[4,1,1,""],NoStackValueError:[4,4,1,""],setup_logging_exception_hook:[4,6,1,""],setup_logging_ipython_exception_hook:[4,6,1,""]},"terra.core.settings":{ENVIRONMENT_VARIABLE:[4,5,1,""],ExpandedString:[4,2,1,""],LazyObject:[4,2,1,""],LazySettings:[4,2,1,""],LazySettingsThreaded:[4,2,1,""],ObjectDict:[4,2,1,""],Settings:[4,2,1,""],TerraJSONEncoder:[4,2,1,""],config_file:[4,6,1,""],filename_suffixes:[4,5,1,""],global_templates:[4,5,1,""],json_include_suffixes:[4,5,1,""],json_load:[4,6,1,""],lock_dir:[4,6,1,""],log_file:[4,6,1,""],logging_hostname:[4,6,1,""],logging_listen_address:[4,6,1,""],need_to_set_virtualenv_dir:[4,6,1,""],processing_dir:[4,6,1,""],settings:[4,5,1,""],settings_dir:[4,6,1,""],settings_property:[4,6,1,""],status_file:[4,6,1,""],stdin_istty:[4,6,1,""],terra_uuid:[4,6,1,""],unittest:[4,6,1,""]},"terra.core.settings.LazyObject":{__contains__:[4,3,1,""],__delattr__:[4,3,1,""],__delitem__:[4,3,1,""],__dir__:[4,3,1,""],__getattr__:[4,3,1,""],__getitem__:[4,3,1,""],__iter__:[4,3,1,""],__len__:[4,3,1,""],__setattr__:[4,3,1,""],__setitem__:[4,3,1,""],_setup:[4,3,1,""]},"terra.core.settings.LazySettings":{_setup:[4,3,1,""],add_templates:[4,3,1,""],configure:[4,3,1,""],configured:[4,3,1,""]},"terra.core.settings.LazySettingsThreaded":{__setattr__:[4,3,1,""],downcast:[4,3,1,""]},"terra.core.settings.ObjectDict":{__dir__:[4,3,1,""],__getattr__:[4,3,1,""],__setattr__:[4,3,1,""],update:[4,3,1,""]},"terra.core.settings.Settings":{__getattr__:[4,3,1,""]},"terra.core.settings.TerraJSONEncoder":{"default":[4,3,1,""],dumps:[4,3,1,""],serializableSettings:[4,3,1,""]},"terra.core.signals":{Signal:[4,2,1,""],logger_configure:[4,5,1,""],logger_reconfigure:[4,5,1,""],post_settings_configured:[4,5,1,""],post_settings_context:[4,5,1,""],receiver:[4,6,1,""]},"terra.core.signals.Signal":{_live_receivers:[4,3,1,""],connect:[4,3,1,""],disconnect:[4,3,1,""],has_listeners:[4,3,1,""],receivers:[4,4,1,""],send:[4,3,1,""],send_robust:[4,3,1,""],sender_receivers_cache:[4,4,1,""],use_caching:[4,4,1,""]},"terra.core.utils":{ClassHandler:[4,2,1,""],Handler:[4,2,1,""],cached_property:[4,2,1,""]},"terra.core.utils.ClassHandler":{_connect_backend:[4,3,1,""]},"terra.core.utils.Handler":{_connect_backend:[4,3,1,""],close:[4,3,1,""]},"terra.core.utils.cached_property":{__get__:[4,3,1,""],func:[4,3,1,""],name:[4,4,1,""]},"terra.executor":{base:[5,0,0,"-"],celery:[6,0,0,"-"],dummy:[5,0,0,"-"],process:[5,0,0,"-"],resources:[5,0,0,"-"],sync:[5,0,0,"-"],thread:[5,0,0,"-"],utils:[5,0,0,"-"]},"terra.executor.base":{BaseExecutor:[5,2,1,""],BaseFuture:[5,2,1,""]},"terra.executor.base.BaseExecutor":{configure_logger:[5,3,1,""],multiprocess:[5,4,1,""],reconfigure_logger:[5,3,1,""]},"terra.executor.celery":{CeleryExecutor:[6,2,1,""],celeryconfig:[6,0,0,"-"],executor:[6,0,0,"-"]},"terra.executor.celery.CeleryExecutor":{configuration_map:[6,3,1,""],configure_logger:[6,3,1,""],multiprocess:[6,4,1,""],reconfigure_logger:[6,3,1,""],shutdown:[6,3,1,""],submit:[6,3,1,""]},"terra.executor.celery.executor":{CeleryExecutor:[6,2,1,""],CeleryExecutorFuture:[6,2,1,""]},"terra.executor.celery.executor.CeleryExecutor":{configuration_map:[6,3,1,""],configure_logger:[6,3,1,""],multiprocess:[6,4,1,""],reconfigure_logger:[6,3,1,""],shutdown:[6,3,1,""],submit:[6,3,1,""]},"terra.executor.celery.executor.CeleryExecutorFuture":{cancel:[6,3,1,""]},"terra.executor.dummy":{DummyExecutor:[5,2,1,""]},"terra.executor.dummy.DummyExecutor":{shutdown:[5,3,1,""],submit:[5,3,1,""]},"terra.executor.process":{ProcessPoolExecutor:[5,2,1,""]},"terra.executor.process.ProcessPoolExecutor":{multiprocess:[5,4,1,""]},"terra.executor.resources":{ProcessLocalStorage:[5,2,1,""],Resource:[5,2,1,""],ResourceError:[5,1,1,""],ResourceManager:[5,2,1,""],ThreadLocalStorage:[5,2,1,""],atexit_resource_release:[5,6,1,""],test_dir:[5,6,1,""]},"terra.executor.resources.ProcessLocalStorage":{instance_id:[5,4,1,""],lock:[5,4,1,""],resource_id:[5,4,1,""]},"terra.executor.resources.Resource":{FileLock:[5,3,1,""],acquire:[5,3,1,""],is_locked:[5,3,1,""],lock_dir:[5,4,1,""],lock_file_name:[5,3,1,""],release:[5,3,1,""]},"terra.executor.resources.ResourceManager":{get_resource:[5,3,1,""],register_resource:[5,3,1,""],resources:[5,4,1,""]},"terra.executor.sync":{SyncExecutor:[5,2,1,""]},"terra.executor.sync.SyncExecutor":{shutdown:[5,3,1,""],submit:[5,3,1,""]},"terra.executor.thread":{ThreadPoolExecutor:[5,2,1,""]},"terra.executor.utils":{Executor:[5,5,1,""],ExecutorHandler:[5,2,1,""]},"terra.executor.utils.ExecutorHandler":{_connect_backend:[5,3,1,""],configuration_map:[5,3,1,""]},"terra.logger":{DEBUG1:[2,5,1,""],DEBUG2:[2,5,1,""],DEBUG3:[2,5,1,""],DEBUG4:[2,5,1,""],Logger:[2,2,1,""],_SetupTerraLogger:[2,2,1,""],_acquireLock:[2,6,1,""],_checkLevel:[2,6,1,""],_demoteLevel:[2,6,1,""],_releaseLock:[2,6,1,""],getLogger:[2,6,1,""]},"terra.logger.Logger":{debug1:[2,3,1,""],debug2:[2,3,1,""],debug3:[2,3,1,""],debug4:[2,3,1,""],fatal:[2,3,1,""],findCaller:[2,3,1,""]},"terra.logger._SetupTerraLogger":{configure_logger:[2,3,1,""],default_formatter:[2,4,1,""],default_stderr_handler_level:[2,4,1,""],default_tmp_prefix:[2,4,1,""],main_log_handler:[2,3,1,""],reconfigure_logger:[2,3,1,""],set_level_and_formatter:[2,3,1,""]},"terra.task":{TerraTask:[2,2,1,""],shared_task:[2,6,1,""],subprocess:[2,6,1,""]},"terra.task.TerraTask":{apply_async:[2,3,1,""],translate_paths:[2,3,1,""]},"terra.utils":{cli:[7,0,0,"-"],workflow:[7,0,0,"-"]},"terra.utils.cli":{ArgumentParser:[7,2,1,""],DbStopAction:[7,2,1,""],FullPaths:[7,2,1,""],FullPathsAppend:[7,2,1,""],clean_path:[7,6,1,""]},"terra.utils.workflow":{AlreadyRunException:[7,1,1,""]},"terra.workflow":{BaseWorkflow:[2,2,1,""],PipelineWorkflow:[2,2,1,""]},"terra.workflow.BaseWorkflow":{run:[2,3,1,""]},"terra.workflow.PipelineWorkflow":{run:[2,3,1,""],service_index:[2,3,1,""]},compute:{arch:[13,8,1,"cmdoption-arg-compute.arch"],virtualenv_dir:[13,8,1,"cmdoption-arg-compute.virtualenv_dir"]},executor:{num_workers:[13,8,1,"cmdoption-arg-executor.num_workers"],type:[13,8,1,"cmdoption-arg-executor.type"]},logging:{date_format:[13,8,1,"cmdoption-arg-logging.date_format"],format:[13,8,1,"cmdoption-arg-logging.format"],format_style:[13,8,1,"cmdoption-arg-logging.format_style"],level:[13,8,1,"cmdoption-arg-logging.level"]},terra:{compute:[3,0,0,"-"],core:[4,0,0,"-"],executor:[5,0,0,"-"],logger:[2,0,0,"-"],settings:[2,5,1,""],task:[2,0,0,"-"],utils:[7,0,0,"-"],workflow:[2,0,0,"-"],zone:[13,8,1,"cmdoption-arg-terra.zone"]}},objnames:{"0":["py","module","Python module"],"1":["py","exception","Python exception"],"2":["py","class","Python class"],"3":["py","method","Python method"],"4":["py","attribute","Python attribute"],"5":["py","data","Python data"],"6":["py","function","Python function"],"7":["std","envvar","environment variable"],"8":["std","cmdoption","program option"]},objtypes:{"0":"py:module","1":"py:exception","2":"py:class","3":"py:method","4":"py:attribute","5":"py:data","6":"py:function","7":"std:envvar","8":"std:cmdoption"},terms:{"10436851":5,"28950776":4,"3rd":11,"798575":5,"9020":[2,4],"abstract":[4,8,9],"case":[2,4,5,13],"catch":4,"class":[2,3,4,5,6,7,8,11,13],"const":7,"default":[2,3,5,7,9,11,12,13],"final":[2,8],"function":[2,3,4,5,8,11],"import":[2,3,4,8,12],"int":5,"long":11,"new":[2,5,10,11],"null":3,"return":[2,3,4,5,6,11,12],"static":[3,4,5,6],"super":3,"throw":4,"transient":4,"true":[3,4,5,6,11],"try":4,"while":[4,5,8,9,11,12],Added:2,Adding:0,And:2,But:8,For:[3,4,5,11,12,13],Not:13,One:4,The:[2,3,5,8,9,10,11,12,13],There:5,These:[4,11,12],Use:3,Used:[3,4],Useful:13,Using:[0,2],Will:[4,6],__contains__:4,__delattr__:4,__delitem__:4,__dict__:4,__dir__:4,__exit__:4,__get__:4,__getattr__:4,__getitem__:4,__init__:[3,5],__iter__:4,__len__:4,__main__:8,__name__:[2,8],__setattr__:4,__setitem__:4,_acquirelock:2,_appendact:7,_base:5,_checklevel:2,_connect_backend:[3,4,5],_demotelevel:2,_dir:[4,12],_docker_volume_flags_r:3,_env_arrai:3,_file:[4,12],_json:4,_live_receiv:4,_local:5,_override_typ:[3,5],_path:[4,12],_releaselock:2,_setup:4,_setupterralogg:2,_thread:5,_use_softfilelock:5,_validate_volum:3,_volum:12,abl:[4,5,8,11],about:[4,5],abov:[2,3],absolut:7,accept:[3,4],access:[2,3,4,5,8,12],accomplish:12,accord:[2,3],acquir:[2,4,5],action:[3,4,7],activ:2,actual:[3,4,5,8,9,13],adapt:3,add:[3,8,10],add_templ:[4,8],add_volum:3,added:4,adding:4,addit:[4,5,11],address:4,adjust:11,advantag:8,after:[2,3,4,5,6,8],again:4,against:[4,11],agnost:[2,12],algorithm:[0,2,4,8,9,12],alia:[4,13],alias:13,all:[2,3,4,5,6,11,12,13],alloc:5,allow:[3,4,5,8],allow_nan:4,along:[4,5],alphanumer:5,alreadi:[2,3,4,5,6],alreadyregisteredexcept:3,alreadyrunexcept:7,also:[2,3,5,11,12],alter:2,altern:6,although:11,altogeth:4,alwai:[2,5,11],among:5,ani:[2,3,4,5,8,11,12],anoth:[2,4,11],anyth:4,anywher:2,api:[5,8,11],app1:8,app1_celeri:8,app2:8,app:[0,2,3,4,5,7,9,11,12,13],appear:2,append:2,appli:12,applic:[4,13],apply_async:[2,6],applyasync_kwarg:6,appnam:8,appropri:[3,4,8],arbitrari:4,arch:[2,3,4,12,13],architectur:[2,3,12,13],area:13,arg:[2,3,4,5,6,7,8],argpars:7,args2:2,argument:[2,3,4,7,11,12],argumentpars:7,arrai:3,array_to_python_ast_list_of_str:[3,8],asctim:[2,4,13],assign:4,associ:[5,6],asyncresult:6,atexit_resource_releas:5,attempt:[4,5],attribut:[4,12,13],automat:[3,4,5,11,12,13],avail:[2,5],awar:11,back:[2,4,12],backend:[3,5],balanc:5,bar:[4,12],bar_path:12,base:[1,2,4,6,7,11],basecomput:3,baseexecutor:[5,6,11],basefutur:[5,6],baseservic:3,baseworkflow:2,bash_sourc:8,basi:5,basic:2,bear:11,becaus:[4,5,11,12],becom:[5,11],been:[2,3,4,5,6,9,11],befor:[2,3,4,5,6,11],behav:4,behavior:[4,5],being:[2,3,4],best:2,better:5,between:[5,6,9,12],bind:11,bool:[4,5],both:[4,5,11],bring:13,brokenprocesspool:11,broker:13,bsh:9,built:[0,12],bypass:[4,5],cach:[3,4],cached_properti:4,call:[2,3,4,5,6,8],caller:2,can:[2,3,4,5,6,8,10,11,12,13],cancel:6,cannot:[3,4,5,6],captur:[2,4],caught:11,celeri:[2,4,5,11,13],celeryconfig:[2,5],celeryexecutor:[6,13],celeryexecutorfutur:6,certain:4,chane:3,chang:[6,11,12],charact:2,check:[4,6],check_circular:4,check_remot:3,child:5,children:4,choic:7,choos:13,circumst:[2,4],classhandl:[4,5],classmethod:[3,4,5],clean:[4,5,6],clean_path:7,cli:[1,2,8,12,13],close:4,cloud:9,cls:[3,4],cluster:9,clutter:4,code:[2,3,11],collid:5,com:[4,5],combin:12,come:5,command:[2,3],common:[3,4,5],commun:[4,5],compat:3,compil:4,complet:6,complic:4,componet:4,compos:[3,9],compose_fil:3,compose_service_nam:3,comput:[0,1,2,4,5,8,11,12],computehandl:3,concret:3,concurr:[5,11,13],condit:[3,11],condition:4,conf:4,config:[3,4],config_fil:[2,4],config_servic:3,configur:[2,3,4,5,12],configuration_map:[5,6,12],configuration_map_servic:[3,12],configurationwarn:4,configure_logg:[2,3,5,6,11],conform:5,confus:5,connect:[3,4,5,11],connectionhandl:4,consequ:5,consid:[4,5],consist:[3,8],contain:[1,2,4,5,9,11,12,13],container_config:3,container_pathlib:3,container_platform:3,container_str:3,containerservic:3,content:[0,1],context:[4,5],contribut:0,control:[2,4,12,13],conveni:4,convert:[4,12],copi:[3,4],core:[1,2,3,5,11,12,13],correct:[3,5,11],correctli:5,could:[4,5,11,13],counter:5,cours:3,crash:[2,11],creat:[2,3,5,9,10,12],create_servic:3,critic:2,current:[3,4,5,8],custom:[0,2,3,4,13],data:[2,4,8,11,12],date15:11,date:13,date_format:[2,4,13],dbstopact:7,deactiv:2,debug1:2,debug2:2,debug3:[2,4],debug4:2,debug:[2,4,9,11],decid:11,decor:[4,8,11],decoupl:4,decrement:5,def:[4,5,8],default_formatt:2,default_index:2,default_set:4,default_stderr_handler_level:2,default_tmp_prefix:2,defin:[3,4,11,13],definit:[3,8,9,13],delai:6,deleg:[2,3],demot:2,depend:13,deploi:[2,12],describ:4,descriptor:4,design:[2,7],dest:7,detail:4,determ:4,determin:5,develop:2,dict:[3,4,12],dictionari:[4,12],differ:[5,11,12,13],dir:[4,5],directli:8,directori:[2,3,4,5,7,8,11],disabl:[2,4],disconnect:4,disk:11,dispatch:4,dispatch_uid:4,displai:2,distinct:4,distribut:11,divid:5,django:4,djangoproject:4,doc:[4,13],docker:[1,2,4,8,9,13],docker_internal_volume_r:3,docker_volume_r:3,document:4,doe:[3,4,5,8,9,11,13],doesn:[4,13],don:[4,5,13],done:[4,11,12],down:[2,3],downcast:[4,5],downsid:5,drive:[3,4],dry:[9,11],due:11,dummi:[1,2,4,9,11,13],dummyexecutor:[5,13],dump:4,dure:[2,4,5],each:[0,3,4,5,9,10,11,13],earli:5,earlier:12,eas:[11,12],easi:[5,11],easier:[3,5],easili:[2,4],edit:5,effect:5,effort:5,either:[3,4,5,11,13],element:4,els:[4,5,12],elsewher:4,emit:2,empti:3,encod:4,end:[12,13],enough:5,ensur:4,ensure_ascii:4,entrypoint:[3,5],env:[3,4,8],environ:[2,3,4,5,8,11,12,13],environment_vari:4,equal:5,equival:11,error:[2,4,6],especi:[4,5],essenti:4,establish:4,etc:[2,3,12],evalu:4,even:[2,4,5,11,12],event:4,ever:[5,11],everi:[5,13],everyth:[2,12],exampl:[3,4,5,8,11],example1:8,example_step:8,example_templ:8,exampleworkflow:8,except:[1,2,3,5,7,11],execut:[2,3,4,5,6,8,11,13],executor:[0,1,2,3,4,8,12],executor_volume_map:2,executorhandl:5,exist:[2,3,5,9],expand:7,expandedstr:4,expect:[2,11],explain:[4,8],explicitli:4,expos:4,express:3,extern:8,extra:2,extrem:2,fact:11,fail:5,fals:[2,3,4,5,6,7,11],fashion:4,fatal:2,fault:[5,11],featur:12,few:5,file:[2,3,4,5,8,11,12],filelock:5,filenam:[2,4,11],filename_suffix:4,filesystem:5,filter:4,find:2,findcal:2,finess:11,finish:[5,6,8],first:[4,11,12,13],flag:3,folder:3,follow:[2,3],foo:[4,12],forc:[5,13],form:[3,5],format:[2,4,13],format_styl:13,formatt:2,found:4,four:2,frame:2,framework:4,friendli:4,from:[2,3,4,5,8,11,12],from_level:2,full:[3,4,8],fulli:[3,5],fullpath:7,fullpathsappend:7,func:4,futur:[5,6,11,13],gener:[2,4],get:[0,3,4,5,8,11],get_absolute_url:4,get_default_service_class:3,get_pars:8,get_resourc:5,get_volume_map:3,getlogg:2,gil:11,give:[3,5],given:[3,5],global:[4,5],global_set:4,global_templ:[4,12],goal:[2,8,9,12],good:11,gpu:5,grid:9,group:3,guidlin:0,halt:11,handl:[3,4,5],handler:[2,3,4,5],happen:[4,5,11],hard:5,hardlock:5,has:[3,4,5,6,9,11,12],has_listen:4,hashabl:4,hasn:4,have:[2,3,4,5,6,8,9,11,12],hello:3,help:[4,7],helper:4,here:[4,12],holder:3,home:7,honor:13,hood:12,hook:11,host:[3,4,5,12,13],host_pathlib:3,host_str:3,hostnam:[2,4,5],how:[2,4,8,11,13],howev:[4,5,11],howto:4,html:[4,13],http:[4,5,13],ideal:4,identifi:4,ignor:5,imag:[8,11],image_fil:11,img123:11,implement:[3,4,6],improperli:4,improperlyconfigur:4,includ:[4,8,11,12,13],inclus:13,incompat:5,increas:5,inde:4,indent:4,independ:8,index:[0,12],individu:4,influenc:5,info:4,inform:[3,11,12],infrastructur:[0,2,12],inherit:[3,5],init:5,initi:[2,4,13],input:[3,12],insensit:13,insert:4,insid:13,inspect:12,instanc:[3,4,5],instance_id:5,instanti:[3,4],instead:[3,4,8,12],integ:[2,5],intend:5,interact:[3,5],interest:[2,4],interfac:[3,5,8,9],intern:[2,3,4,5,6],interpret:2,invok:4,ipc:5,ipython:4,is_lock:5,isn:4,isol:5,item:[4,5],items_integ:5,iter:[4,5],its:[4,5,9,11,13],itself:[3,9],job:5,jpg:11,json:[4,8,12],json_include_suffix:4,json_load:4,jsonencod:4,junk:3,just:[3,4,5,8,11,13],just_singularity_funct:9,justfil:[3,8],keep:5,kei:[3,4,12],keyword:[4,5,11,12],know:[4,5],known:5,kwarg:[2,3,4,5,6,7],kwargs2:2,lai:8,larger:4,last:[3,8,12,13],late:5,later:4,layer:[8,9,13],lazi:4,lazili:4,lazyobject:4,lazyset:4,lazysettingsthread:[4,5],least:3,less:5,let:[4,8],level:[2,4,13],levelnam:[2,4,13],librari:[11,13],lifetim:5,like:[2,4,11,13],limit:[5,11],line:[2,3],linux:[3,5],list:[2,3,4,12],listen:4,listen_address:[2,4],littl:11,live:4,load:[3,4,5],load_servic:3,local:[3,5,9,11],local_must_exist:3,locat:13,lock:[2,4,5],lock_dir:[2,4,5],lock_file_nam:5,log:[0,2,4,5,9,11,12],log_fil:[2,4],log_level:2,logger:[1,4,11],logger_configur:4,logger_reconfigur:4,logging_hostnam:[2,4],logging_listen_address:[2,4],logrecord:13,loop:4,loos:4,loosli:4,machin:13,made:8,magic:4,mai:[2,4,5],main:[4,8,11,12,13],main_log_handl:2,mainli:[3,5],maintain:5,make:[4,5,8,11],manag:5,mani:4,manual:4,map:[3,4,12],master:13,match:12,math:2,matter:3,max_tim:4,max_work:[5,6],maximum:13,messag:[2,3,4,5,13],metadata:4,metavar:7,method:[4,5,6,8,11,12],might:[3,4],miss:13,mitm:4,mix:11,mock:4,mock_foo:4,model:3,modul:[0,1],more:[2,4,5,7,11],most:[2,3],mostli:4,mount:[3,11,12],msg:2,multipl:[0,2,4,5,7,11,12],multiprocess:[5,6,11,13],multithread:[5,11],must:[4,5,8,11],my_set:12,mymodel:4,name:[2,3,4,5,8,11,12],name_or_class:3,narg:7,necessari:[2,4,5,8],need:[0,2,3,4,5,8,11,12,13],need_to_set_virtualenv_dir:4,nest:[4,5,12],nested_upd:12,network:[4,5],new_cal:4,newli:2,next:8,nfs:11,no_remot:3,no_stack_except:4,nocopi:3,node:11,non:[3,4,8],none:[2,3,4,5,6,7,8,13],normal:[4,5,11],nostackexcept:4,nostackvalueerror:4,notat:13,note:[2,4,5],noth:[4,5,13],notifi:4,notimplementederror:4,now:2,num_work:[2,4,13],number:[2,5,13],nutshel:4,obj:4,object:[2,3,4,5],objectdict:4,occur:[2,4,5],off:[3,4,5],offer:[8,9],often:[5,8,11],old:3,onc:[2,4,7,12],one:[0,2,4,5,6,7,11,12,13],ones:12,onli:[2,3,4,5,7,11,13],onto:11,oper:4,opt:12,option:[3,4,5,6,8,10,13],option_str:7,order:[4,8,11,12],org:[4,13],origin:[2,3,4],other:[3,4,5,6,11,13],otherwis:[4,5,6],out:[4,5,8,13],outliv:11,output:[2,3,12,13],overload:4,overrid:[3,4,5,12],overridden:[3,4],override_typ:[3,4,5],overwrit:[2,4],own:[5,9,11,13],packag:[0,1],package_nam:2,page:0,pair:[3,4,12],parallel:[2,5,8,11],param:4,paramet:[2,3,4,5,6],parent:5,pars:[3,4],parse_arg:8,part:[2,3,5,8],parti:11,partial:[3,5],particular:[3,4],pass:[3,4,5,6],patch:[4,11],patch_volum:3,path:[3,5,7,8,9,11,13],pathlib:3,pathlib_map:3,pattern:[4,12],payload:2,per:[4,5,11],perform:8,physic:11,pickl:11,pickleabl:5,pid:5,piec:4,pipelin:[2,13],pipelineworkflow:[2,13],pipenv:[2,8],place:[3,4],platform:[3,9],plugin:8,point:4,popen:3,popul:4,port:[2,4],possibl:[3,4,6,11],post_:3,post_delet:4,post_run:3,post_sav:4,post_settings_configur:4,post_settings_context:[4,6],postdelai:6,potenti:[5,12],practic:11,pre_:3,pre_run:3,pre_run_task:6,predelai:6,prefer:5,prefix:[2,3],prefork:11,prepend:3,prepopul:12,prevent:4,primari:8,primarili:3,print:[3,4,5,13],prior:[2,4,5],privat:3,process:[1,2,3,4,11,13],processing_dir:[2,4],processlocalstorag:5,processnam:[2,4],processor:5,processpoolexecutor:[2,4,5,13],product:11,programat:3,project1:11,propag:4,properti:[2,4,5],propertymock:4,provid:5,providing_arg:4,proxi:4,pure:3,purpos:[2,12],put:4,python:[2,3,5,8,11,12,13],qualifi:[3,5],queue:[5,6],quintessenti:3,race:11,rais:[3,4,5,11],random:2,rang:5,rare:[2,4],rather:[4,5],reach:5,read:[11,13],realli:2,reason:[4,5],receiv:4,reclaim:[5,6],recommend:4,reconfigur:4,reconfigure_logg:[2,3,5,6,11],recov:3,recurs:4,redefin:4,redi:13,refer:[4,10,11],referenc:4,regex:3,regist:[3,4,5],register_resourc:5,regular:3,rel:[7,11],releas:[2,5],remain:4,remot:3,remov:[2,4],remove_servic:3,repeat:5,repetit:2,replac:4,replai:2,repo:8,report:5,repres:[4,5,12,13],requir:[5,7,11],rerun:8,reserv:5,resolv:[3,4,5],resourc:[1,2,4,6],resource_id:5,resource_index:5,resource_nam:5,resourceerror:5,resourcemanag:5,respond:4,respons:[3,4],result:[4,5],resum:[2,4,8],retri:6,retriev:4,retry_kwarg:6,retry_queu:6,return_valu:4,reverse_compute_volume_map:2,rewrit:0,robust:11,rogu:5,role:10,root:2,rout:4,rst:10,run:[0,2,3,4,5,6,7,8,9,11,12,13],run_servic:3,runner:[3,5,8,9,13],runtim:2,safe:[4,5,6],sai:8,same:[2,3,4,5,12],save:2,scenario:5,scope:[4,5],screen:[2,4],search:0,second:[2,4,12],section:5,see:[2,3,4,11],seen:2,seg:[5,11],select:13,self:[2,3,4,5,8,11],send:4,send_robust:4,sender:[2,3,4,5,6],sender_receivers_cach:4,sens:5,sensibl:4,sent:[3,4],separ:[3,4],sequenc:[4,5],serial:[2,4,11],serializ:[4,11],serializableset:4,server:[2,4],servic:[2,3,4,5,8,9,11,12,13],service1:8,service1_imag:8,service_end:[2,4,13],service_index:2,service_info:[3,5,6],service_nam:2,service_start:[2,4,13],servicerunfail:3,set:[0,1,2,3,5,6,8,10,11],set_array_default:8,set_level_and_formatt:2,setting_nam:10,settings_dir:[2,4,5],settings_fil:8,settings_properti:4,setup:[2,4,8,11,12],setup_logging_exception_hook:4,setup_logging_ipython_exception_hook:4,sever:[5,6],share:[2,3,5],shared_task:[2,11],shell:2,shorthand:5,should:[2,3,4,5,8,10,11,12,13],shouldn:4,show:8,shutdown:[5,6],side:5,signal:[1,2],signal_receiv:4,signals_receiv:4,similar:4,simpl:[2,4,5],simpli:[5,9,11,12],simplier:4,simultan:5,sinc:[3,4,11],singl:[3,4,5,8,11],singleton:5,singular:[1,2,9,13],singular_defaultifi:9,skip:[8,13],skipkei:4,slave:3,small:5,snippet:5,soft:5,softfilelock:5,some:[4,5,11,13],somehow:4,someth:[3,4,11,12],something_ast:3,sometim:5,soon:11,sort_kei:4,sourc:[2,3],spam:2,spawn:5,special:[6,11],specif:[2,3,4,5,8],specifi:[2,3,4,13],src1:8,src2:8,stack:[2,4],stack_info:2,stacklevel:2,stackoverflow:[4,5],stage:[7,8,13],standard:3,start:[0,3,4,5,11,13],start_servic:3,state:6,statement:[2,4],statu:4,status_fil:[2,4],stdin_istti:4,stdout:2,step:3,still:[4,13],stop_servic:3,storag:5,store:[4,5],str:[2,3,4,5],string:[3,4,13],strong:4,structur:[4,5,12],stuff:[4,8],style:[2,3,4,13],subclass:4,submit:[5,6],submodul:[1,8],subpackag:1,subprocess:2,subsequ:4,subset:4,success:5,successfulli:8,suffix:[4,12],sugar:6,suggest:5,suitabl:3,suppli:5,support:[0,4,5,9,11],sure:5,symbol:5,sync:[1,2,11,13],syncexecutor:[5,13],synchron:[5,11],system:[2,3,5],tabl:11,take:8,taken:4,target:3,task:[1,4,5,6,8,11,12,13],task_id:2,technic:8,tell:4,templat:4,temporari:[2,4],termin:4,terra:[9,10,11],terra_:12,terra_app1:8,terra_app1_cwd:8,terra_app1_dir:8,terra_app1_dir_dock:8,terra_app1_just_set:8,terra_app2:8,terra_app2_cwd:8,terra_app2_dir:8,terra_app2_dir_dock:8,terra_app_prefix:8,terra_celery_includ:8,terra_celery_main_nam:8,terra_celery_servic:8,terra_disable_settings_dump:4,terra_disable_terra_log:4,terra_initial_tmp_:2,terra_initial_tmp_xxxxxxxx:2,terra_lock_dir:4,terra_log:2,terra_resolve_hostnam:4,terra_settings_fil:[2,8,12],terra_terra_volum:8,terra_unittest:[2,4],terra_uuid:[2,4],terrajsonencod:4,terratask:[2,5,11],test:[2,5,12,13],test_dir:5,than:[3,4,5,7,11],thei:[2,3,4,5,8,11],them:[4,8,10],themselv:12,thi:[2,3,4,5,6,8,9,11,12,13],thin:8,those:12,though:4,thread:[1,2,11,13],threadlocalstorag:5,threadpoolexecutor:[5,13],three:[2,13],through:4,thrown:[3,5,7],thu:[5,11],time:[2,3,4,5,6,11],to_level:2,todo:[9,12],toler:5,too:5,tool:[9,11,12],topic:4,total:5,trace:4,track:5,translat:[2,3,4,8,9,11],translate_path:2,translate_settings_path:3,treat:5,trigger:[4,6],trivial:4,tty:4,tupl:[3,4,12],turn:[4,7,11],two:[2,3,5,8],txt:12,type:[0,2,3,4,5,7,11,13],typeerror:4,typic:[5,8,9,11],uncaught:4,under:[3,4],underli:2,underneath:12,unevalu:4,unexpect:4,unhandl:4,uninstanti:4,unintend:5,uniqu:[4,5],unit:2,unittest:[2,4],unless:[2,4],unlik:5,unload:5,unlock:5,unset:4,unspecifi:4,until:[4,5,6],updat:[4,5,13],update_delai:6,url:4,usag:1,use:[2,3,4,5,8,9,11,12,13],use_cach:4,use_softfilelock:5,used:[2,3,4,5,6,7,8,9,10,11,12,13],useful:[2,4,8],user:[2,4,7],uses:[4,5,11],using:[2,3,4,5,6,8,9,11,12,13],usual:[3,4,12],util:[1,2,8,11,12],uuid:[2,4],valid:3,valu:[3,4,5,11,12,13],valueerror:[3,5],variabl:[2,3,4,8,12,13],verbos:2,version:5,via:[2,3,5,8,12],virtual:[3,13],virtualenv:[1,2,4,8,9,13],virtualenv_dir:[3,4,13],volum:[3,4,12],volume_map:[2,3,4],vsi:12,vsi_common:8,wai:[2,3,5,11,12,13],wait:[5,6],want:[3,4,5,13],warn:[2,4,13],weak:4,weakkeydictionari:4,weakref:4,were:5,what:[0,3,5,9,11],whatev:4,when:[2,3,4,5,7,9,10,11,12,13],where:[2,4,5,12,13],whether:[2,4],which:[3,4,5,9,11,13],whose:3,why:5,window:[3,5],within:12,without:[0,2,5],won:4,work:[4,5,7,11],worker:[4,5,11,13],worker_pool:11,workflow:[0,1,3,8],would:[2,4,5,8,9,11],wrap:[3,4,11],wrapper:[4,8],write:[4,7],writeabl:4,you:[3,4,5,8,11,13],your:[2,4,8,11,13],zero:[3,5],zone:[2,4,5,13]},titles:["Welcome to Terra\u2019s documentation!","terra","terra package","terra.compute package","terra.core package","terra.executor package","terra.executor.celery package","terra.utils package","Terra Apps","Compute","Contributing Guidlines","Executor","What is Terra","Terra Settings"],titleterms:{"default":4,Adding:8,The:4,Using:[4,9,11],advanc:12,alter:4,app:8,avail:4,base:[3,5],basic:4,built:[9,11],celeri:6,celeryconfig:6,celeryexecutor:11,cli:7,code:4,comput:[3,9,13],contain:3,content:[2,3,4,5,6,7],contribut:10,core:4,custom:[9,11],design:4,docker:3,dockercomput:9,document:[0,10],dummi:[3,5],dummycomput:9,dummyexecutor:11,except:4,executor:[5,6,11,13],get:12,guidlin:10,indic:0,log:13,logger:2,modul:[2,3,4,5,6,7],packag:[2,3,4,5,6,7],path:12,process:5,processpoolexecutor:11,python:4,resourc:5,runtim:4,set:[4,12,13],signal:4,singular:3,singularitycomput:9,start:12,submodul:[2,3,4,5,6,7],subpackag:[2,5],sync:5,syncexecutor:11,tabl:0,task:2,templat:12,terra:[0,1,2,3,4,5,6,7,8,12,13],terra_settings_fil:4,thread:5,threadpoolexecutor:11,translat:12,usag:[2,12],util:[3,4,5,7],virtualenv:3,virtualenvcomput:9,welcom:0,what:12,without:4,workflow:[2,7,13]}})