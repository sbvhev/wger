# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

from rest_framework import viewsets
from rest_framework.decorators import link
from rest_framework.decorators import api_view
from rest_framework.response import Response

from wger.nutrition.api.serializers import NutritionPlanSerializer
from wger.nutrition.forms import UnitChooserForm

from wger.nutrition.models import Ingredient
from wger.nutrition.models import Meal
from wger.nutrition.models import MealItem
from wger.nutrition.models import WeightUnit
from wger.nutrition.models import IngredientWeightUnit
from wger.nutrition.models import NutritionPlan

from wger.utils.language import load_ingredient_languages
from wger.utils.viewsets import WgerOwnerObjectModelViewSet


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for ingredient objects
    '''
    model = Ingredient
    ordering_fields = '__all__'
    filter_fields = ('carbohydrates',
                     'carbohydrates_sugar',
                     'creation_date',
                     'energy',
                     'fat',
                     'fat_saturated',
                     'fibres',
                     'name',
                     'protein',
                     'sodium',
                     'status',
                     'update_date',
                     'language',
                     'user',
                     'license',
                     'license_author')

    @link()
    def get_values(self, request, pk):
        '''
        Calculates the nutritional values for current ingredient and
        the given amount and unit.

        This function basically just performs a multiplication (in the model), and
        is a candidate to be moved to pure AJAX calls, however doing it like this
        keeps the logic nicely hidden and respects the DRY principle.
        '''

        result = {'energy': 0,
                  'protein': 0,
                  'carbohydrates': 0,
                  'carbohydrates_sugar': 0,
                  'fat': 0,
                  'fat_saturated': 0,
                  'fibres': 0,
                  'sodium': 0,
                  'errors': []}
        ingredient = self.get_object()

        form = UnitChooserForm(request.GET)

        if form.is_valid():

            # Create a temporary MealItem object
            if form.cleaned_data['unit']:
                unit_id = form.cleaned_data['unit'].id
            else:
                unit_id = None

            item = MealItem()
            item.ingredient = ingredient
            item.weight_unit_id = unit_id
            item.amount = form.cleaned_data['amount']

            result = item.get_nutritional_values()
        else:
            result['errors'] = form.errors

        return Response(result)


@api_view(['GET'])
def search(request):
    '''
    Searches for ingredients.

    This format is currently used by the ingredient search autocompleter
    '''
    q = request.GET.get('term', None)
    results = []
    if not q:
        return Response(results)

    languages = load_ingredient_languages(request)

    # Perform the search
    q = request.GET.get('term', '')
    ingredients = Ingredient.objects.filter(name__icontains=q,
                                            language__in=languages,
                                            status__in=Ingredient.INGREDIENT_STATUS_OK)

    results = []
    for ingredient in ingredients:
        ingredient_json = {'id': ingredient.id,
                           'name': ingredient.name,
                           'value': ingredient.name}
        results.append(ingredient_json)

    return Response(results)


class WeightUnitViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for weight unit objects
    '''
    model = WeightUnit
    ordering_fields = '__all__'
    filter_fields = ('language',
                     'name')


class IngredientWeightUnitViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for many-to-many table ingredient-weight unit objects
    '''
    model = IngredientWeightUnit
    ordering_fields = '__all__'
    filter_fields = ('amount',
                     'gramm',
                     'ingredient',
                     'unit')


class NutritionPlanViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for nutrition plan objects
    '''
    model = NutritionPlan
    serializer_class = NutritionPlanSerializer
    is_private = True
    ordering_fields = '__all__'
    filter_fields = ('creation_date',
                     'language',
                     'description',
                     'has_goal_calories')

    def get_queryset(self):
        '''
        Only allow access to appropriate objects
        '''
        return NutritionPlan.objects.filter(user=self.request.user)

    def pre_save(self, obj):
        '''
        Set the owner
        '''
        obj.user = self.request.user

    @link()
    def nutritional_values(self, request, pk):
        '''
        Return an overview of the nutritional plan's values
        '''
        return Response(NutritionPlan.objects.get(pk=pk).get_nutritional_values())


class MealViewSet(WgerOwnerObjectModelViewSet):
    '''
    API endpoint for meal objects
    '''
    model = Meal
    is_private = True
    ordering_fields = '__all__'
    filter_fields = ('order',
                     'plan',
                     'time')

    def get_queryset(self):
        '''
        Only allow access to appropriate objects
        '''
        return Meal.objects.filter(plan__user=self.request.user)

    def pre_save(self, obj):
        '''
        Set the order
        '''
        obj.order = 1

    def get_owner_objects(self):
        '''
        Return objects to check for ownership permission
        '''
        return [(NutritionPlan, 'plan')]

    @link()
    def nutritional_values(self, request, pk):
        '''
        Return an overview of the nutritional plan's values
        '''
        return Response(Meal.objects.get(pk=pk).get_nutritional_values())


class MealItemViewSet(WgerOwnerObjectModelViewSet):
    '''
    API endpoint for meal item objects
    '''
    model = MealItem
    is_private = True
    ordering_fields = '__all__'
    filter_fields = ('amount',
                     'ingredient',
                     'meal',
                     'order',
                     'weight_unit')

    def get_queryset(self):
        '''
        Only allow access to appropriate objects
        '''
        return MealItem.objects.filter(meal__plan__user=self.request.user)

    def pre_save(self, obj):
        '''
        Set the order
        '''
        obj.order = 1

    def get_owner_objects(self):
        '''
        Return objects to check for ownership permission
        '''
        return [(Meal, 'meal')]

    @link()
    def nutritional_values(self, request, pk):
        '''
        Return an overview of the nutritional plan's values
        '''
        return Response(MealItem.objects.get(pk=pk).get_nutritional_values())
