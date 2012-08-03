# This file is part of Workout Manager.
# 
# Foobar is free software: you can redistribute it and/or modify
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

from manager.models import Exercise, ExerciseComment, ExerciseCategory
from django.contrib import admin

class ExerciseCommentInline(admin.TabularInline): #admin.StackedInline
    model = ExerciseComment
    extra = 1

class ExerciseAdmin(admin.ModelAdmin):
    #fields = ['name',]
    
    inlines = [ExerciseCommentInline]


    
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(ExerciseCategory)