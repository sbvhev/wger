# This file is part of Workout Manager.
# 
# Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License


"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse

from exercises.models import Exercise
from exercises.models import ExerciseCategory

class WorkoutManagerTestCase(TestCase):
    fixtures = ['tests-user-data', 'test-exercises', ]
    
    def user_login(self, user='admin'):
        """Login the user, by default as 'admin'
        """
        self.client.login(username=user, password='%(user)s%(user)s' % {'user': user})
        
    def user_logout(self):
        """Visit the logout page
        """
        self.client.logout()

        
class ExerciseIndexTestCase(WorkoutManagerTestCase):
   
    def test_exercise_index(self):
        """Tests the exercise overview page"""
        
        response = self.client.get(reverse('exercises.views.exercise_overview'))
        
        # Page exists
        self.assertEqual(response.status_code, 200)
        
        # Correct tab is selected
        self.assertEqual(response.context['active_tab'], 'exercises')
        
        # Correct categories are shown
        category_1 = response.context['categories'][0]
        self.assertEqual(category_1.id, 2)
        self.assertEqual(category_1.name, "Another category")
        
        category_2 = response.context['categories'][1]
        self.assertEqual(category_2.id, 3)
        self.assertEqual(category_2.name, "Yet another category")
        
        # Correct exercises in the categories
        exercises_1 = category_1.exercise_set.all()
        exercise_1 = exercises_1[0]
        exercise_2 = exercises_1[1]
        self.assertEqual(exercise_1.id, 2)
        self.assertEqual(exercise_1.name, "A very cool exercise")
        
        self.assertEqual(exercise_2.id, 1)
        self.assertEqual(exercise_2.name, "An exercise")
        
        
    def test_exercise_detail(self):
        """Tests the exercise details page
        """
        
        response = self.client.get(reverse('exercises.views.exercise_view', kwargs={'id': 1}))
        self.assertEqual(response.status_code, 200)
        
        # Correct tab is selected
        self.assertEqual(response.context['active_tab'], 'exercises')
        
        # Exercise loaded correct muscles
        exercise_1 = response.context['exercise']
        self.assertEqual(exercise_1.id, 1)
        
        muscles = exercise_1.muscles.all()
        muscle_1 = muscles[0]
        muscle_2 = muscles[1]
        
        self.assertEqual(muscle_1.id, 1)
        self.assertEqual(muscle_2.id, 2)
        
        # Ensure that non-existent exercises throw a 404.
        response = self.client.get(reverse('exercises.views.exercise_view', kwargs={'id': 42}))
        self.assertEqual(response.status_code, 404)
        

class ExercisecommentsTestCase(WorkoutManagerTestCase):
    
    def exercisecomment_fail(self):
        """Tests the exercise comments (fails because of permissions)"""
        
        # Load the exercise
        exercise_1 = Exercise.objects.get(pk=1)
        comments = exercise_1.exercisecomment_set.all()
        self.assertEqual(len(comments), 1)
        
        # Post a comment
        response = self.client.post(reverse('exercises.views.exercise_view', kwargs={'id': 1}), 
                                    {'comment': 'a new cool comment'})
        self.assertEqual(response.status_code, 200)
        
        comments = exercise_1.exercisecomment_set.all()
        self.assertEqual(len(comments), 1)

    
    def test_exercisecomment_no_authorized(self):
        """Tests the exercise comments"""
        
        self.user_login('test')
        self.exercisecomment_fail()
        self.user_logout()
    
    def test_exercisecomment_not_logged_in(self):
        """Tests the exercise comments"""
        
        self.user_logout()
        self.exercisecomment_fail()
        
    
    def test_exercisecomment_authorized(self):
        """Tests the exercise comments"""
        
        self.user_login()
        
        # Load the exercise
        exercise_1 = Exercise.objects.get(pk=1)
        
        # Comments are loaded
        comments = exercise_1.exercisecomment_set.all()
        comment_1 = comments[0]
        self.assertEqual(comment_1.id, 1)
        self.assertEqual(comment_1.comment, "test 123")
        self.assertEqual(len(comments), 1)
        
        # Post a comment
        response = self.client.post(reverse('exercises.views.exercise_view', kwargs={'id': 1}), 
                                    {'comment': 'a new cool comment'})
        comments = exercise_1.exercisecomment_set.all()
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(comments), 2)
        
        # Post an empty comment and check it doesn't get added
        response = self.client.post(reverse('exercises.views.exercise_view', kwargs={'id': 1}), 
                                    {'comment': ''})
        comments = exercise_1.exercisecomment_set.all()
        
        self.assertEqual(len(comments), 2)
        self.user_logout()
        
class ExercisesTestCase(WorkoutManagerTestCase):
    """Exercise test case"""
    
    
    def add_exercise_user_fail(self):
        """Helper function to test adding exercises by users that aren't
        authorized
        """
        
        # Add an exercise
        count_before = Exercise.objects.count()
        response = self.client.post(reverse('exercises.views.exercise_edit', kwargs= {'id': ''}), 
                                        {'category': 2,
                                         'name': 'my test exercise',
                                         'muscles': [1, 2]})
        count_after = Exercise.objects.count()
        
        # Exercise was not added
        self.assertEqual(count_before, count_after)
        
        self.assertTrue(reverse('manager.views.login') in response['location'])

    def test_add_exercise_user_no_rights(self):
        """Tests adding an exercise with a user without enough rights to do this"""
        
        self.user_login('test')
        self.add_exercise_user_fail()
        self.user_logout()
    
    def test_add_exercise_no_user(self):
        """Tests adding an exercise with a logged out (anonymous) user"""
        
        self.user_logout()
        self.add_exercise_user_fail()
        self.user_logout()
        
        
    def test_add_exercise_administrator_user(self):
        """Tests adding/editing an exercise with a user with enough rights to do this"""
        
        # Log in as 'admin'
        self.user_login()
        
        # Add an exercise
        response = self.client.post(reverse('exercises.views.exercise_edit', kwargs = {'id': ''}), 
                                        {'category': 2,
                                         'name': 'my test exercise',
                                         'muscles': [1, 2]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Exercise.objects.count(), 4, 'Exercise was not added')
        
        # Exercise was saved
        response = self.client.get(reverse('exercises.views.exercise_view', kwargs = {'id': 4}))
        self.assertEqual(response.status_code, 200)
        
        # Navigation tab
        self.assertEqual(response.context['active_tab'], 'exercises')
        
        exercise_1 = Exercise.objects.get(pk = 4)
        self.assertEqual(exercise_1.name, 'my test exercise')
        
        # Wrong category - adding
        response = self.client.post(reverse('exercises.views.exercise_edit', kwargs = {'id': ''}), 
                                        {'category': 111,
                                         'name': 'my test exercise',
                                         'muscles': [1, 2]})
        self.assertTrue(response.context['edit_form'].errors['category'])
        
        # Wrong category - editing
        response = self.client.post(reverse('exercises.views.exercise_edit', kwargs = {'id': '1'}), 
                                        {'category': 111,
                                         'name': 'my test exercise',
                                         'muscles': [1, 2]})
        self.assertTrue(response.context['edit_form'].errors['category'])
        
        
        # No muscles - adding
        response = self.client.post(reverse('exercises.views.exercise_edit', kwargs = {'id': ''}), 
                                        {'category': 1,
                                         'name': 'my test exercise',
                                         'muscles': []})
        self.assertTrue(response.context['edit_form'].errors['muscles'])
        
        # No muscles - editing
        response = self.client.post(reverse('exercises.views.exercise_edit', kwargs = {'id': '1'}), 
                                        {'category': 1,
                                         'name': 'my test exercise',
                                         'muscles': []})
        self.assertTrue(response.context['edit_form'].errors['muscles'])
        
        
        #print response.context['edit_form'].errors
        #print response['location']
        
        self.user_logout()


    def delete_exercise(self, fail=True):
        """Helper function to test deleting exercises"""
        
        # The exercise exists
        response = self.client.get(reverse('exercises.views.exercise_view', kwargs={'id': 3}))
        self.assertEqual(response.status_code, 200)
        
        # Delete the exercise
        count_before = Exercise.objects.count()
        response = self.client.get(reverse('exercises.views.exercise_delete', kwargs={'id': 3}))
        count_after = Exercise.objects.count()
        
        # There is a redirect
        self.assertEqual(response.status_code, 302)
        
        # Check the deletion
        if fail:
            self.assertEqual(count_before, count_after, 'Exercise was deleted')
        else:
            self.assertTrue(count_before > count_after, 'Exercise was not deleted')
        
        
    def test_delete_exercise_anonymous(self):
        """Test deleting an exercise by an anonymous user"""
        
        self.delete_exercise()
        
        
    def test_delete_exercise_unauthorized(self):
        """Test deleting an exercise by an unauthorized user"""
        
        self.user_login('test')
        self.delete_exercise()
        self.user_logout()
    
    def test_delete_exercise_authorized(self):
        """Test deleting an exercise by an authorized user"""
                
        self.user_login()
        self.delete_exercise(fail=False)        
        self.user_logout()

class ExerciseCategoryTestCase(WorkoutManagerTestCase):
    """Exercise category test case"""
  
    def delete_category(self, fail = False):
        """Helper function to test deleting categories"""
        
        # Delete the category
        count_before =  ExerciseCategory.objects.count()
        response = self.client.get(reverse('exercises.views.exercise_category_delete',
                                           kwargs={'id': 4}))
        count_after = ExerciseCategory.objects.count()
        
        # There is a redirect
        self.assertEqual(response.status_code, 302)
        
        # Check the deletion
        if fail:
            self.assertEqual(count_before,
                             count_after,
                             'Category was deleted by unauthorzed user')
        else:
            self.assertTrue(count_before > count_after,
                            'Category was not deleted by authorized user')
        
        
    def test_delete_category_unauthorized(self):
        """Test deleting a category by an unauthorized user"""
        
        self.user_login('test')
        self.delete_category(fail=True)
        self.user_logout()
    
    def test_delete_category_anonymous(self):
        """Test deleting a category by an anonymous user"""
        
        self.user_logout()
        self.delete_category(fail=True)
        self.user_logout()
    
    def test_delete_category_authorized(self):
        """Test deleting a category by an authorized user"""
        
        self.user_login()
        self.delete_category()
        self.user_logout()
    
    
    def edit_category(self, fail = False):
        """Helper function to test editing categories"""
        
        category = ExerciseCategory.objects.get(pk = 3)
        old_name = category.name
        
        response = self.client.post(reverse('exercises.views.exercise_category_edit',
                                           kwargs={'id': 3}),
                                   {'name': 'A different name'})
        
        # There is a redirect
        self.assertEqual(response.status_code, 302)
        
        category = ExerciseCategory.objects.get(pk = 3)
        new_name = category.name
        
        
        # Did it work
        if fail:
            self.assertEqual(old_name,
                             new_name,
                             'Category was edited by unauthorzed user')
        else:
            self.assertTrue(old_name != new_name,
                            'Category wasnt deleted by unauthorzed user')
        
        
        # No name
        if not fail:
            response = self.client.post(reverse('exercises.views.exercise_category_edit',
                                           kwargs={'id': 3}),
                                        {'name': ''})

            self.assertTrue(response.context['category_form'].errors['name'])
        
    def test_edit_category_unauthorized(self):
        """Test deleting a category by an unauthorized user"""
        
        self.user_login('test')
        self.edit_category(fail=True)
        self.user_logout()
    
    def test_edit_category_anonymous(self):
        """Test deleting a category by an anonymous user"""
        
        self.user_logout()
        self.edit_category(fail=True)
        self.user_logout()
    
    def test_edit_category_authorized(self):
        """Test deleting a category by an authorized user"""
        
        self.user_login()
        self.edit_category()
        self.user_logout()
    
