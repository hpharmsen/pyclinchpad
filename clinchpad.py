import requests
from configparser import ConfigParser


class Clinchpad:
    def __init__(self):
        self.base_url = 'https://www.clinchpad.com/api/v1/'

        config = ConfigParser()
        config.read('clinchpad.ini')
        self.api_key = config.get('api', 'key')

        self._pipelines = None  # Cache

    ########## G E N E R A L ##########

    def get(self, path):
        return requests.get(self.base_url + path, auth=('api-key', self.api_key)).json()

    def post(self, path, json):
        return requests.post(
            self.base_url + path, json=json, auth=('api-key', self.api_key)
        ).json()

    def put(self, path, data):
        return requests.put(self.base_url + path, data=data, auth=('api-key', self.api_key)).json()

    def delete(self, path):
        return requests.delete(self.base_url + path, auth=('api-key', self.api_key)).json()

    ########## U S E R S ##########

    def users(self):
        return self.get('users')

    ########## P I P E L I N E ##########

    def pipelines(self):
        if self._pipelines:
            return self._pipelines
        else:
            return self.get('pipelines')

    def pipeline(self, pipeline_name):
        pipelines = [p for p in self.pipelines() if p['name'] == pipeline_name]
        assert pipelines, f'Pipeline {pipeline_name} does not exist'
        return pipelines[0]

    ########## L E A D S ##########

    def leads(self, pipeline_name, stages=[]):
        if type(stages) == type('string'):
            stages = [stages]
        pipeline_id = self.pipeline(pipeline_name)['_id']
        result = self.get('leads?size=999&pipeline_id=' + pipeline_id)
        if stages:
            result = [r for r in result if r.get('stage') and r['stage']['name'] in stages]
        return result

    def update_lead(self, lead_id, data):
        return self.put(f'leads/{lead_id}', data)

    def move_lead(self, lead, pipeline_name, new_stage):
        stage_id = self.stage_by_name(pipeline_name, new_stage)['_id']
        return self.update_lead(lead['_id'], {'stage_id': stage_id})

    ########## F I E L D S ##########

    def fields(self, lead):
        return self.get(f'leads/{lead["_id"]}/fields')

    def delete_field(self, lead, field):
        return self.delete(f'leads/{lead["_id"]}/fields/{field["_id"]}')

    ########## N O T E S ##########

    def notes(self, lead):
        return self.get(f'leads/{lead["_id"]}/notes?size=999')

    def find_note_having(self, lead, predicate, keep_only_last=False):
        all_results = []
        for note in self.notes(lead):
            content = note['content']
            result = predicate(content)
            if result:
                if keep_only_last:
                    # Create a list of all resuls found
                    all_results += [[note, result]]
                else:
                    # return just the first one found
                    return result
        if all_results:
            for note, result in all_results[:-1]:
                print('Deleting double note', result)
                self.delete_note(lead, note)
            return all_results[-1][1]
        return None

    def add_note(self, lead, new_text):
        return self.post(
            f'leads/{lead["_id"]}/notes',
            {'content': new_text, 'user_id': '5c4db105f986030014662372'},
        )

    def update_note(self, lead, note, new_text):
        return self.put(f'leads/{lead["_id"]}/notes/{note["_id"]}', {'content': new_text})

    def delete_note(self, lead, note):
        return self.delete(f'leads/{lead["_id"]}/notes/{note["_id"]}')

    ########## S T A G E ##########

    def stage_by_name(self, pipeline_name, stage_name):
        pipeline_id = self.pipeline(pipeline_name)['_id']
        stages = self.get(f'/pipelines/{pipeline_id}/stages')
        for stage in stages:
            if stage['name'] == stage_name:
                return stage
        assert False, f'Stage {stage_name} not found in pipeline {pipeline_name}'
