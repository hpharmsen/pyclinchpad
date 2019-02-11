import requests
from configparser import ConfigParser
from dateutil.parser import parse


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
        '''
        Get users data structure like in https://clinchpad.com/api/docs/users
        '''
        return self.get('users')

    ########## P I P E L I N E ##########

    def pipelines(self):
        """
        Singleton. If the list of pipelines has already been fetched, return it
        Otherwise, retrieve the pipelines first.
        """
        if not self._pipelines:
            self._pipelines = self.get('pipelines')
        return self._pipelines

    def pipeline(self, pipeline_name):
        """
        Find a pipleline by name
        """
        pipelines = [p for p in self.pipelines() if p['name'] == pipeline_name]
        assert pipelines, f'Pipeline {pipeline_name} does not exist'
        return pipelines[0]

    ########## L E A D S ##########

    def leads(self, pipeline_name, stages=[]):
        """
        Get the leads from a given pipeline as in https://clinchpad.com/api/docs/leads
        :param pipeline_name: string
        :param stages: list of names of stages (optional)
        todo: pagination. Currently only one page with max 999 leads is returned.
        """
        if type(stages) == type('string'):
            stages = [stages]
        pipeline_id = self.pipeline(pipeline_name)['_id']
        result = self.get('leads?size=999&pipeline_id=' + pipeline_id)
        if stages:
            result = [r for r in result if r.get('stage') and r['stage']['name'] in stages]
        return result

    def lead_by_id(self, id):
        """
        Returns the lead with the specified id
        """
        return self.get(f'leads/{id}')

    def update_lead(self, lead, data):
        """
        Update a leads fields.
        e.g. To set the leaads value: update_lead( mylead, {value=20000} )
        """
        return self.put(f'leads/{lead["_id"]}', data)

    def move_lead(self, lead, pipeline_name, new_stage):
        """
        Move a lead to a new stage
        e.g. To move lead to negociation stage: move_lead( mylead, 'negociation' )
        """
        stage_id = self.stage_by_name(pipeline_name, new_stage)['_id']
        return self.update_lead(lead['_id'], {'stage_id': stage_id})

    ########## F I E L D S ##########

    def fields(self, lead):
        """
        Get all fields from a lead
        """
        return self.get(f'leads/{lead["_id"]}/fields')

    def delete_field(self, lead, field):
        """
        Delete a field in a lead
        """
        return self.delete(f'leads/{lead["_id"]}/fields/{field["_id"]}')

    ########## N O T E S ##########

    def notes(self, lead):
        """
        Get all notes from a given lead
        """
        return self.get(f'leads/{lead["_id"]}/notes?size=999')

    def find_note_having(self, lead, predicate, keep_only_last=False):
        """
        Advanced not finding
        :param lead: Lead to search in
        :param predicate: function that gets lead and list of notes and returns note values that comply
        :param keep_only_last: If multiple notes match the predicate, return the last and delete the rest
        :return: Whatever the predicates returned. Or None if none matches.
        """
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
                self.delete_note(lead, note)
            return all_results[-1][1]
        return None

    def add_note(self, lead, new_text):
        """
        Add a new note to a given lead
        """
        return self.post(
            f'leads/{lead["_id"]}/notes',
            {'content': new_text, 'user_id': '5c4db105f986030014662372'},
        )

    def update_note(self, lead, note, new_text):
        """
        Update an existing note
        """
        return self.put(f'leads/{lead["_id"]}/notes/{note["_id"]}', {'content': new_text})

    def delete_note(self, lead, note):
        """
        Delete given note
        """
        return self.delete(f'leads/{lead["_id"]}/notes/{note["_id"]}')

    ########## S T A G E S ##########

    def stage_by_name(self, pipeline_name, stage_name):
        """
        Find a stage by name
        """
        pipeline = self.pipeline(pipeline_name)
        stages = self.get(f'/pipelines/{pipeline["_id"]}/stages')
        for stage in stages:
            if stage['name'] == stage_name:
                return stage
        assert False, f'Stage {stage_name} not found in pipeline {pipeline_name}'

    ########## A C T I V I T I E S ##########

    def activities(
        self, pipeline=None, lead=None, activity_types=[], start_date=None, end_date=None
    ):
        """
        Get activities filteres by various parameters
        :param pipeline: return only activities from this pipeline (optional)
        :param lead: return only activities from this lead (optional)
        :param activity_types: return only these activity types. See https://clinchpad.com/api/docs/activities
        :param start_date: return only activities from this date onwards
        :param end_date: return only activities before this date
        :return: list of activities. See https://clinchpad.com/api/docs/activities for the format
        """

        if lead:
            path = f'leads/{lead["_id"]}/activities'
        else:
            path = '/activities'
        path += '?size=999'  # todo: implement pagination
        if activity_types:
            path += '&filter_type=' + ','.join(activity_types)

        activities = self.get(path)

        if pipeline:
            activities = [a for a in activities if a['pipeline']['_id'] == pipeline['_id']]

        if start_date:
            sd = parse(start_date).astimezone()
            activities = [a for a in activities if parse(a['created_at']) >= sd]

        if end_date:
            ed = parse(end_date).astimezone()
            activities = [a for a in activities if parse(a['created_at']) <= ed]

        return activities
