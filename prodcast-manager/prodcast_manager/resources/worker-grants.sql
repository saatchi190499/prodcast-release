BEGIN;
GRANT USAGE ON SCHEMA public TO prodcast_worker_01, prodcast_worker_02;
GRANT SELECT ON
 apiapp_unit_system, apiapp_unit_type, apiapp_unit_definition,
 apiapp_unit_category, apiapp_unit_system_category_definition,
 apiapp_workflow, apiapp_workflow_scheduler, apiapp_data_source_component,
 apiapp_scenarios, apiapp_scenario_component_link, apiapp_data_source,
 apiapp_object_type, apiapp_object_instance, apiapp_object_type_property
 TO prodcast_worker_01, prodcast_worker_02;
GRANT SELECT (id,username) ON auth_user TO prodcast_worker_01, prodcast_worker_02;
GRANT SELECT,INSERT,UPDATE ON apiapp_workflow_run TO prodcast_worker_01, prodcast_worker_02;
GRANT INSERT ON apiapp_audit_log TO prodcast_worker_01, prodcast_worker_02;
GRANT SELECT,INSERT ON apiapp_scenariolog,apiapp_workflow_scheduler_log TO prodcast_worker_01, prodcast_worker_02;
GRANT UPDATE (status,start_date,end_date) ON apiapp_scenarios TO prodcast_worker_01, prodcast_worker_02;
DO $$
BEGIN
 IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='apiapp_scenarios' AND column_name='server') THEN
  GRANT UPDATE (server) ON apiapp_scenarios TO prodcast_worker_01, prodcast_worker_02;
 END IF;
END $$;
GRANT SELECT,INSERT,UPDATE,DELETE ON apiapp_mainclass,apiapp_mainclass_history TO prodcast_worker_01, prodcast_worker_02;
GRANT UPDATE (id) ON apiapp_data_source_component TO prodcast_worker_01, prodcast_worker_02;
GRANT USAGE,SELECT ON SEQUENCE
 apiapp_workflow_run_id_seq,apiapp_audit_log_id_seq,apiapp_scenariolog_id_seq,
 apiapp_workflow_scheduler_log_id_seq,apiapp_mainclass_data_set_id_seq,
 apiapp_mainclass_history_id_seq TO prodcast_worker_01,prodcast_worker_02;
COMMIT;
