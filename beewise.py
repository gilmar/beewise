"""
BeeWise - A Spelling Practice Application
"""

import pygame
import pyttsx3
import sys
import csv
import random
import time
import os
from rapidfuzz.distance import DamerauLevenshtein

# ============================================================================
# INITIALISATION
# ============================================================================

# Initialize pygame
pygame.init()
# Initialise pyttsx3
engine = pyttsx3.init()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Window dimensions
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Color palette - Neo-brutalism style inspired by bumblebees
# Bright yellow, vibrant orange, bold black, and creamy whites
BACKGROUND_COLOR = (255, 250, 235)  # Pale cream/yellow (bee-inspired)
PRIMARY_COLOR = (255, 220, 0)  # Bright sunny yellow (bumblebee body)
ACCENT_COLOR = (255, 152, 0)  # Vibrant orange (bee accent color)
TEXT_COLOR = (0, 0, 0)  # Pure black (bee stripes and outlines)
CORRECT_COLOR = (180, 220, 0)  # Yellow-green (complements bee yellow)
ERROR_COLOR = (220, 80, 50)  # Red-orange (complements bee orange)
INPUT_BOX_COLOR = (255, 255, 255)  # Pure white (bee wing color)
BORDER_COLOR = (0, 0, 0)  # Pure black for thick borders (bee outline)

# Fonts
TITLE_FONT_SIZE = 48
WORD_FONT_SIZE = 56
INPUT_FONT_SIZE = 42
MESSAGE_FONT_SIZE = 32
BUTTON_FONT_SIZE = 32

# Text to voice
SPEAKING_RATE = 125

# Number of words per session
NUM_WORDS_PER_SESSION = 3

# CSV file containing words
WORD_BANK_CSV_FILENAME = "words_mixed_levels.csv"

# Directory for storing user records (one CSV file per user)
USERS_DIRECTORY = "users"

# ============================================================================
# SETUP
# ============================================================================

# Create the game window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("BeeWise - Spelling Practice")

# Create font objects
title_font = pygame.font.SysFont(None, TITLE_FONT_SIZE)
word_font = pygame.font.Font(None, WORD_FONT_SIZE)
button_font = pygame.font.SysFont(None, BUTTON_FONT_SIZE)

input_font = pygame.font.Font(None, INPUT_FONT_SIZE)
message_font = pygame.font.Font(None, MESSAGE_FONT_SIZE)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Speak rate
engine.setProperty("rate", SPEAKING_RATE)

# ============================================================================
# CLASSES
# ============================================================================


class Word:
    """
    The Word class represents a single word with its level and source.
    This class stores all the information we know about a word from the CSV file:
    - The word itself (the text to spell)
    - Its difficulty level (1, 2, 3, etc.)
    - Its source (where the word came from, like "eowl")
    """
    
    def __init__(self, word, level, source):
        """
        Create a new Word object.
        word: The word text (string, e.g., "python")
        level: The difficulty level (integer, e.g., 1, 2, 3)
        source: Where the word came from (string, e.g., "eowl")
        """
        # Store the word text (convert to lowercase for consistency)
        self.word = word.lower().strip()
        
        # Store the difficulty level (convert to integer if needed)
        self.level = int(level)
        
        # Store the source (where this word came from)
        self.source = source.strip()
    
    def __str__(self):
        """
        Return a string representation of the Word.
        This is useful for printing or displaying the word.
        """
        return f"Word('{self.word}', level={self.level}, source='{self.source}')"
    
    def compare(self, other_word):
        """
        Compare this word with another word and return a similarity score.
        The score is based on the Damerau-Levenshtein distance, which measures
        how many operations (insertions, deletions, substitutions, transpositions)
        are needed to transform one word into another.
        
        The score is normalized between 0.0 and 1.0, where:
        - 1.0 means the words are identical
        - 0.0 means the words are completely different
        - Values in between indicate partial similarity
        
        Parameters:
        other_word: The word to compare against (string or Word object).
                   If it's a Word object, we use its .word attribute.
                   If it's a string, we compare directly (it will be lowercased).
        
        Returns:
        float: A similarity score between 0.0 (completely different) and 1.0 (identical)
        """
        # Extract the word text if other_word is a Word object, otherwise use it as-is
        if isinstance(other_word, Word):
            # If it's a Word object, get its .word attribute
            other_word_text = other_word.word
        else:
            # If it's a string, convert to lowercase and strip whitespace for consistency
            other_word_text = str(other_word).lower().strip()
        
        # Calculate the normalized similarity score using Damerau-Levenshtein distance
        # This gives us a score from 0.0 (completely different) to 1.0 (identical)
        # The normalized_similarity function internally uses the distance and converts it
        similarity_score = DamerauLevenshtein.normalized_similarity(
            self.word, 
            other_word_text
        )
        
        return similarity_score

class User:
    """
    The User class represents a player who uses the BeeWise spelling practice application.
    This class stores the user's name and keeps track of all their spelling practice records
    across multiple sessions.
    
    Each record stores information about one word attempt:
    - session_id: Which practice session this word was from
    - word_typed: What the user typed (their spelling attempt)
    - correct_word: The correct spelling of the word
    - level: The difficulty level of the word (1, 2, 3, etc.)
    - similarity_score: How similar the typed word is to the correct word (0.0 to 1.0)
    """
    
    def __init__(self, name, users_directory="users"):
        """
        Create a new User object and load existing records from CSV file.
        name: The user's name (string, e.g., "Alice" or "Bob")
        users_directory: The directory where user CSV files are stored (default: "users")
        """
        # Store the user's name (strip whitespace for consistency)
        self.name = name.strip()
        
        # Create the filename from the user's name:
        # 1. Convert to lowercase
        # 2. Replace spaces with underscores
        # 3. Remove any non-alphanumeric characters (keep only letters, numbers, and underscores)
        # For example: "Alice" -> "alice.csv", "Bob Smith" -> "bob_smith.csv", "John's" -> "johns.csv"
        name_lower = self.name.lower().strip()
        
        # Replace spaces with underscores
        name_with_underscores = name_lower.replace(' ', '_')
        
        # Build filename by keeping only alphanumeric characters and underscores
        # We'll go through each character and only keep letters, numbers, and underscores
        safe_filename = ""
        for char in name_with_underscores:
            # Check if character is alphanumeric (letter or number) or underscore
            if char.isalnum() or char == '_':
                safe_filename += char
        
        # Add .csv extension
        filename = safe_filename + ".csv"
        
        # Create the full path to the CSV file in the users directory
        # For example: "users/alice.csv"
        self.csv_filename = os.path.join(users_directory, filename)
        
        # Create the users directory if it doesn't exist
        # os.makedirs creates the directory (and any parent directories needed)
        # exist_ok=True means it won't raise an error if the directory already exists
        os.makedirs(users_directory, exist_ok=True)
        
        # Start with an empty list of records
        # Each record will be a dictionary containing all the information about one word attempt
        self.records = []
        
        # Load existing records from the CSV file (if it exists)
        # This will also create the file if it doesn't exist yet
        self.load_from_csv()
        
        # Debug: Print user creation summary
        print(f"[DEBUG] User: Created user '{self.name}' with {len(self.records)} existing records")
        print(f"[DEBUG] User: CSV file: {self.csv_filename}")
    
    def add_record(self, session_id, word_typed, correct_word, level, similarity_score):
        """
        Add a new record to track a word attempt.
        This method stores all the information about one spelling attempt in the records list.
        
        Parameters:
        session_id: The unique identifier for the practice session (usually from GameSession.id)
        word_typed: What the user typed (string, e.g., "pithon")
        correct_word: The correct spelling (string, e.g., "python")
        level: The difficulty level of the word (integer, e.g., 1, 2, 3)
        similarity_score: How similar typed word is to correct word (float, 0.0 to 1.0)
                         A score of 1.0 means perfect match, 0.0 means completely different
        """
        # Create a dictionary to store all the information about this word attempt
        # A dictionary is like a labeled box that holds multiple pieces of information
        # Each piece has a label (the key) and a value
        record = {
            "session_id": session_id,           # Which session this word was from
            "word_typed": word_typed.lower().strip(),      # What user typed (normalize to lowercase)
            "correct_word": correct_word.lower().strip(),  # Correct spelling (normalize to lowercase)
            "level": int(level),                # Difficulty level (ensure it's an integer)
            "similarity_score": float(similarity_score)    # Similarity score (ensure it's a float)
        }
        
        # Add this record to the user's list of records
        # The records list will grow as the user practices more words
        self.records.append(record)
        
        # Debug: Print when records are added
        print(f"[DEBUG] User.add_record(): Added record - word: '{correct_word}', typed: '{word_typed}', "
              f"level: {level}, similarity: {similarity_score:.3f}")
    
    def get_level(self):
        """
        Calculate and return the user's level based on their spelling practice records.
        The user's level is determined by counting how many words they spelled correctly
        at each difficulty level, and returning the level with the maximum count.
        
        A word is considered correct if the similarity_score is 1.0 (perfect match).
        
        Returns:
        int: The user's level (1, 2, 3, etc.). Returns 1 if there are no records or no correct words.
        """
        # If there are no records, return level 1 (beginner level)
        if len(self.records) == 0:
            print(f"[DEBUG] User.get_level(): No records found, returning level 1")
            return 1
        
        # Dictionary to count how many correct words at each level
        # The key is the level number, the value is the count of correct words at that level
        level_counts = {}
        
        # Go through all records and count correct words by level
        for record in self.records:
            # A word is correct if similarity_score is exactly 1.0 (perfect match)
            if record['similarity_score'] >= 1.0:
                level = record['level']
                
                # If we haven't seen this level before, initialize the count to 0
                if level not in level_counts:
                    level_counts[level] = 0
                
                # Increment the count for this level
                level_counts[level] += 1
        
        # If no words were spelled correctly, return level 1
        if len(level_counts) == 0:
            return 1
        
        # Find the level with the maximum count
        # We'll iterate through all levels and keep track of which one has the highest count
        max_level = 1  # Start with level 1 as default
        max_count = 0  # Start with 0 as the initial maximum count
        
        # Check each level to see which has the most correct words
        for level in level_counts:
            count = level_counts[level]
            # If this level has more correct words, it becomes the new max
            if count > max_count:
                max_count = count
                max_level = level
        
        # Return the level with the maximum count
        print(f"[DEBUG] User.get_level(): Level counts: {level_counts}, returning level {max_level}")
        return max_level
    
    def get_mispelled_words_with_averages(self):
        """
        Calculate the average similarity score for each word the user has attempted.
        Words with average score less than 0.99 are considered mispelled.
        
        Returns:
        list: A list of tuples (correct_word, average_score, level), sorted by average_score in ascending order.
              Lower scores (more mistakes) come first.
        """
        # Dictionary to store all scores for each word
        # Key: correct_word (the word text)
        # Value: list of similarity scores for that word
        word_scores = {}
        
        # Dictionary to store the level for each word (all attempts of same word should have same level)
        word_levels = {}
        
        # Go through all records and collect scores for each word
        for record in self.records:
            correct_word = record['correct_word']
            similarity_score = record['similarity_score']
            level = record['level']
            
            # If this is the first time we've seen this word, initialize its score list
            if correct_word not in word_scores:
                word_scores[correct_word] = []
                word_levels[correct_word] = level
            
            # Add this attempt's score to the word's score list
            word_scores[correct_word].append(similarity_score)
        
        # Calculate average score for each word and filter for mispelled words
        mispelled_words = []
        
        for correct_word in word_scores:
            # Calculate average of all scores for this word
            scores_list = word_scores[correct_word]
            total_score = 0.0
            for score in scores_list:
                total_score += score
            
            average_score = total_score / len(scores_list)
            
            # Only include words with average score less than 0.99 (mispelled)
            if average_score < 0.99:
                level = word_levels[correct_word]
                mispelled_words.append((correct_word, average_score, level))
        
        # Sort by average_score in ascending order (lowest scores first)
        # This means words with more mistakes will be selected first
        # We'll restructure the list to put the score first, sort, then restructure back
        # This avoids using lambda functions while keeping the code clear
        
        # Step 1: Create a new list with score first for easy sorting
        # Each item will be (average_score, correct_word, level)
        temp_list = []
        for item in mispelled_words:
            correct_word = item[0]
            average_score = item[1]
            level = item[2]
            temp_list.append((average_score, correct_word, level))
        
        # Step 2: Sort the list (Python sorts tuples by first element by default)
        temp_list.sort()
        
        # Step 3: Restructure back to (correct_word, average_score, level)
        sorted_mispelled_words = []
        for item in temp_list:
            average_score = item[0]
            correct_word = item[1]
            level = item[2]
            sorted_mispelled_words.append((correct_word, average_score, level))
        
        # Debug: Print mispelled words found
        print(f"[DEBUG] User.get_mispelled_words_with_averages(): Found {len(sorted_mispelled_words)} mispelled words")
        if sorted_mispelled_words:
            print(f"[DEBUG] User.get_mispelled_words_with_averages(): Top 5 worst: {sorted_mispelled_words[:5]}")
        
        return sorted_mispelled_words
    
    def load_from_csv(self):
        """
        Load user records from the CSV file.
        If the file doesn't exist, it will be created with just the header row.
        """
        try:
            # Try to open and read the CSV file
            with open(self.csv_filename, 'r', encoding='utf-8') as csv_file:
                # Create a CSV reader that will read each row as a dictionary
                csv_reader = csv.DictReader(csv_file)
                
                # Read each row from the CSV file
                for row in csv_reader:
                    # Create a record dictionary with all the information
                    record = {
                        "session_id": float(row['session_id']),      # Convert to float (was stored as timestamp)
                        "word_typed": row['word_typed'].lower().strip(),
                        "correct_word": row['correct_word'].lower().strip(),
                        "level": int(row['level']),                   # Convert to integer
                        "similarity_score": float(row['similarity_score'])  # Convert to float
                    }
                    # Add this record to the user's records list
                    self.records.append(record)
            
            # Debug: Print how many records were loaded
            if len(self.records) > 0:
                print(f"[DEBUG] User.load_from_csv(): Loaded {len(self.records)} records from {self.csv_filename}")
        
        except FileNotFoundError:
            # If the CSV file doesn't exist, create it with the header row
            # This is expected on first run - we'll create the file structure
            with open(self.csv_filename, 'w', encoding='utf-8', newline='') as csv_file:
                # Create a CSV writer
                csv_writer = csv.writer(csv_file)
                
                # Write the header row with column names
                csv_writer.writerow(['session_id', 'word_typed', 'correct_word', 'level', 'similarity_score'])
            
            # The file is now created but empty - user has no records yet
            print(f"Created new user records file: {self.csv_filename}")
        
        except Exception as e:
            # If any other error occurs, print it but continue with empty records
            print(f"Error reading CSV file '{self.csv_filename}': {e}")
            self.records = []
    
    def save_to_csv(self):
        """
        Save all user records to the CSV file.
        """
        try:
            # Open the CSV file for writing (this will overwrite the existing file)
            with open(self.csv_filename, 'w', encoding='utf-8', newline='') as csv_file:
                # Create a CSV writer
                csv_writer = csv.writer(csv_file)
                
                # Write the header row
                csv_writer.writerow(['session_id', 'word_typed', 'correct_word', 'level', 'similarity_score'])
                
                # Write all records for this user
                for record in self.records:
                    # Write one row with all the information
                    csv_writer.writerow([
                        str(record['session_id']),      # Convert to string for CSV
                        record['word_typed'],
                        record['correct_word'],
                        str(record['level']),           # Convert to string for CSV
                        str(record['similarity_score']) # Convert to string for CSV
                    ])
        
        except Exception as e:
            # If there's an error writing, print it
            print(f"Error saving to CSV file '{self.csv_filename}': {e}")
    
    def __str__(self):
        """
        Return a string representation of the User.
        This is useful for printing or displaying user information.
        Shows the user's name and how many records they have.
        """
        num_records = len(self.records)
        return f"User(name='{self.name}', records={num_records})"

class GameEngine:
    """
    The GameEngine class loads words from a CSV file and can create GameSession objects.
    Think of it as the word bank - it stores all available words and provides
    random selections for practice sessions.
    """
    
    def __init__(self, csv_filename):
        """
        Initialize the game engine by loading words from a CSV file.
        csv_filename: The path to the CSV file containing words (e.g., "words_mixed_levels.csv")
        """
        # Store all words from the CSV file
        self.all_words = []
        
        # Open and read the CSV file
        try:
            with open(csv_filename, 'r', encoding='utf-8') as csv_file:
                # Create a CSV reader that will read each row as a dictionary
                csv_reader = csv.DictReader(csv_file)
                
                # Read each row and create a Word object
                for row in csv_reader:
                    # Extract word, level, and source from the CSV row
                    word_text = row['word'].strip()
                    level = row['level'].strip()
                    source = row['source'].strip()
                    # Only add non-empty words
                    if word_text:
                        # Create a Word object with all the information from the CSV
                        word_obj = Word(word_text, level, source)
                        self.all_words.append(word_obj)
        
        except FileNotFoundError:
            # If the CSV file doesn't exist, print an error and use empty list
            print(f"Error: Could not find file '{csv_filename}'")
            self.all_words = []
        
        except Exception as e:
            # If any other error occurs, print it and use empty list
            print(f"Error reading CSV file: {e}")
            self.all_words = []
        
        # Debug: Print word loading summary
        print(f"[DEBUG] GameEngine: Loaded {len(self.all_words)} words from '{csv_filename}'")
        
        # Debug: Count words by level
        level_counts = {}
        for word_obj in self.all_words:
            level = word_obj.level
            if level not in level_counts:
                level_counts[level] = 0
            level_counts[level] += 1
        
        if level_counts:
            print(f"[DEBUG] GameEngine: Words by level: {level_counts}")
        else:
            print(f"[DEBUG] GameEngine: No words loaded!")
    
    def get_max_level(self):
        """
        Find the maximum difficulty level in the word bank.
        This is useful for determining the highest level available when selecting words.
        
        Returns:
        int: The maximum level found in all_words. Returns 1 if no words are available.
        """
        # If there are no words, return level 1
        if len(self.all_words) == 0:
            return 1
        
        # Start with the first word's level as the maximum
        max_level = self.all_words[0].level
        
        # Go through all words and find the highest level
        for word_obj in self.all_words:
            if word_obj.level > max_level:
                max_level = word_obj.level
        
        return max_level
    
    def get_words_by_level(self, level):
        """
        Get all words from the word bank that match a specific difficulty level.
        
        Parameters:
        level: The difficulty level to filter by (integer, e.g., 1, 2, 3)
        
        Returns:
        list: A list of Word objects that have the specified level
        """
        words_at_level = []
        
        # Go through all words and collect those at the specified level
        for word_obj in self.all_words:
            if word_obj.level == level:
                words_at_level.append(word_obj)
        
        return words_at_level
    
    def create_session(self, user_obj=None):
        """
        Create a new GameSession with NUM_WORDS_PER_SESSION words selected based on user history.
        The selection follows this strategy:
        - One third from previously mispelled words (average score < 0.99)
        - One third from one level above the user's level (or max level if user is at max)
        - One third from the same level as the user's level
        
        Parameters:
        user_obj: A User object containing the user's practice history (optional).
                  If None or user has no records, only level 1 words will be selected.
        
        Returns:
        A new GameSession object ready to use
        """
        # If no user provided or user has no records, use level 1 words only
        if user_obj is None or len(user_obj.records) == 0:
            print(f"[DEBUG] GameEngine.create_session(): No user or no records, using level 1 words only")
            level_1_words = self.get_words_by_level(1)
            print(f"[DEBUG] GameEngine.create_session(): Selected {len(level_1_words)} level 1 words")
            return GameSession(level_1_words)
        
        # Calculate how many words we need for each category
        # We'll divide NUM_WORDS_PER_SESSION into three equal parts
        words_per_category = NUM_WORDS_PER_SESSION // 3
        remainder = NUM_WORDS_PER_SESSION % 3
        
        # The selected words list that we'll build
        selected_words = []
        
        # Get the user's current level
        user_level = user_obj.get_level()
        
        # Get the maximum level available in the word bank
        max_level = self.get_max_level()
        
        # Debug: Print session creation strategy
        print(f"[DEBUG] GameEngine.create_session(): Creating session for user '{user_obj.name}'")
        print(f"[DEBUG] GameEngine.create_session(): User level: {user_level}, Max level available: {max_level}")
        print(f"[DEBUG] GameEngine.create_session(): Target words per session: {NUM_WORDS_PER_SESSION}")
        
        # Category 1: Previously mispelled words (one third)
        # Get mispelled words sorted by average score (lowest scores first)
        mispelled_list = user_obj.get_mispelled_words_with_averages()
        
        # Convert mispelled words (which are strings) to Word objects
        # We need to find the Word objects from all_words that match
        mispelled_word_objects = []
        for correct_word, avg_score, word_level in mispelled_list:
            # Find the Word object in all_words that matches this word
            # Note: avg_score and word_level are part of the tuple but we primarily
            # match by correct_word text. The word_level could be used to verify
            # we're getting the right word if there are duplicates at different levels.
            for word_obj in self.all_words:
                if word_obj.word == correct_word:
                    mispelled_word_objects.append(word_obj)
                    break  # Found it, move to next mispelled word
        
        # Select the lowest-ranked mispelled words (first words_per_category)
        num_from_mispelled = words_per_category
        if remainder > 0:
            num_from_mispelled += 1
            remainder -= 1
        
        if len(mispelled_word_objects) >= num_from_mispelled:
            # We have enough mispelled words, take the first num_from_mispelled
            selected_words.extend(mispelled_word_objects[:num_from_mispelled])
            print(f"[DEBUG] GameEngine.create_session(): Category 1 (mispelled): Selected {num_from_mispelled} words")
        else:
            # Not enough mispelled words, take all we have
            # The rest will be filled from same-level words in the Category 3 section below
            selected_words.extend(mispelled_word_objects)
            print(f"[DEBUG] GameEngine.create_session(): Category 1 (mispelled): Selected {len(mispelled_word_objects)} words "
                  f"(only {len(mispelled_word_objects)} available, needed {num_from_mispelled})")
        
        # Category 2: Words from one level above user (or max level if user is at max)
        # Determine the target level (one above user, or max if user is already at max)
        target_level = user_level + 1
        if target_level > max_level:
            target_level = max_level
        
        # Get all words at the target level
        words_at_target_level = self.get_words_by_level(target_level)
        
        # Remove words we've already selected (avoid duplicates)
        available_at_target = []
        for word_obj in words_at_target_level:
            # Check if this word is already in selected_words
            already_selected = False
            for selected_word_obj in selected_words:
                if selected_word_obj.word == word_obj.word:
                    already_selected = True
                    break
            
            if not already_selected:
                available_at_target.append(word_obj)
        
        # Select random words from target level
        num_from_higher = words_per_category
        if remainder > 0:
            num_from_higher += 1
            remainder -= 1
        
        if len(available_at_target) >= num_from_higher:
            # We have enough words, randomly select
            selected_words.extend(random.sample(available_at_target, num_from_higher))
            print(f"[DEBUG] GameEngine.create_session(): Category 2 (level {target_level}): Selected {num_from_higher} words")
        else:
            # Not enough words at higher level, take all available
            selected_words.extend(available_at_target)
            print(f"[DEBUG] GameEngine.create_session(): Category 2 (level {target_level}): Selected {len(available_at_target)} words "
                  f"(only {len(available_at_target)} available, needed {num_from_higher})")
        
        # Category 3: Words from same level as user
        # Get all words at the user's level
        words_at_user_level = self.get_words_by_level(user_level)
        
        # Remove words we've already selected (avoid duplicates)
        available_at_user_level = []
        for word_obj in words_at_user_level:
            # Check if this word is already in selected_words
            already_selected = False
            for selected_word_obj in selected_words:
                if selected_word_obj.word == word_obj.word:
                    already_selected = True
                    break
            
            if not already_selected:
                available_at_user_level.append(word_obj)
        
        # Calculate how many more words we need to reach NUM_WORDS_PER_SESSION
        num_needed = NUM_WORDS_PER_SESSION - len(selected_words)
        
        # Also account for any words we couldn't get from mispelled category
        # (This was handled earlier, but we need to make sure we fill up)
        
        # Select random words from user's level to fill remaining slots
        if num_needed > 0 and len(available_at_user_level) > 0:
            if len(available_at_user_level) >= num_needed:
                # We have enough words, randomly select
                selected_words.extend(random.sample(available_at_user_level, num_needed))
                print(f"[DEBUG] GameEngine.create_session(): Category 3 (level {user_level}): Selected {num_needed} words")
            else:
                # Not enough words at user level, take all available
                selected_words.extend(available_at_user_level)
                print(f"[DEBUG] GameEngine.create_session(): Category 3 (level {user_level}): Selected {len(available_at_user_level)} words "
                      f"(only {len(available_at_user_level)} available, needed {num_needed})")
        
        # If we still don't have enough words, fill the rest with any available words
        # (This handles edge cases where there aren't enough words in the requested categories)
        if len(selected_words) < NUM_WORDS_PER_SESSION:
            # Get all words that haven't been selected yet
            remaining_words = []
            for word_obj in self.all_words:
                already_selected = False
                for selected_word_obj in selected_words:
                    if selected_word_obj.word == word_obj.word:
                        already_selected = True
                        break
                
                if not already_selected:
                    remaining_words.append(word_obj)
            
            # Calculate how many more we need
            still_needed = NUM_WORDS_PER_SESSION - len(selected_words)
            
            # Randomly select from remaining words
            if len(remaining_words) >= still_needed:
                selected_words.extend(random.sample(remaining_words, still_needed))
                print(f"[DEBUG] GameEngine.create_session(): Filled remaining slots: Selected {still_needed} words from any level")
            else:
                # If we still don't have enough, just use what's available
                selected_words.extend(remaining_words)
                print(f"[DEBUG] GameEngine.create_session(): Filled remaining slots: Selected {len(remaining_words)} words "
                      f"(only {len(remaining_words)} available, needed {still_needed})")
        
        # Shuffle the selected words so they don't appear in a predictable order
        # (mispelled first, then higher level, then same level)
        random.shuffle(selected_words)
        
        # Debug: Print final word selection
        print(f"[DEBUG] GameEngine.create_session(): Final selection: {len(selected_words)} words")
        for i, word_obj in enumerate(selected_words):
            print(f"[DEBUG] GameEngine.create_session():   Word {i+1}: '{word_obj.word}' (level {word_obj.level})")
        
        # Create and return a GameSession with the selected words
        # We need to modify GameSession.__init__ to accept a pre-selected word list
        # For now, we'll create a temporary GameSession and replace its word_list
        session = GameSession(self.all_words)  # Temporary, will be modified
        session.word_list = selected_words
        
        # Update current_word to the first word in the selected list
        if selected_words:
            session.current_word = selected_words[0]
        else:
            session.current_word = None
        
        return session


class GameSession:
    """
    The GameSession class manages a single practice session with NUM_WORDS_PER_SESSION random words.
    It tracks which word the player is currently spelling and keeps track of progress.
    """
    
    def __init__(self, all_words):
        """
        Initialize a new game session by selecting NUM_WORDS_PER_SESSION random words.
        all_words: A list of all available words (usually from GameEngine)
        """
        # Create a unique ID for this session using the current timestamp
        # time.time() returns the number of seconds since January 1, 1970 (Unix epoch)
        # This gives us a unique identifier for when the session was created
        self.id = time.time()
        
        # Get random words from the available word list
        # We use random.sample() which picks random items without duplicates
        if len(all_words) >= NUM_WORDS_PER_SESSION:
            # If we have NUM_WORDS_PER_SESSION or more words, pick exactly NUM_WORDS_PER_SESSION random ones
            self.word_list = random.sample(all_words, NUM_WORDS_PER_SESSION)
        else:
            # If we have fewer than NUM_WORDS_PER_SESSION words, just use all available words
            self.word_list = all_words.copy()
        
        # Which word in the session we're currently on (starts at 0 for the first word)
        self.word_index = 0
        
        # The actual word the player needs to spell (starts with first word)
        # current_word is now a Word object, not just a string
        if self.word_list:
            self.current_word = self.word_list[0]
            # Debug: Print session creation
            print(f"[DEBUG] GameSession: Created session {self.id:.2f} with {len(self.word_list)} words")
            if self.current_word:
                print(f"[DEBUG] GameSession: First word: '{self.current_word.word}' (level {self.current_word.level})")
        else:
            # If no words available, set to None (this will be handled in the game loop)
            self.current_word = None
            print(f"[DEBUG] GameSession: Warning - Created session with no words!")
        
        # What the user has typed so far (starts empty)
        self.user_input = ""
        
        # The game can be in two states: "INPUT" (user is typing) or "FEEDBACK" (showing results)
        self.state = "INPUT"
        
        # Whether the user's answer was correct or not
        self.is_correct = False
        
        # Track words entered by the user, correct words, and similarity scores
        # These lists will store one entry for each word in the session
        # Each entry corresponds to the word at the same index in word_list
        self.words_entered = []  # List of strings: what the user typed for each word
        self.correct_words = []  # List of strings: the correct spelling for each word
        self.similarity_scores = []  # List of floats: similarity score (0.0 to 1.0) for each word
    
    def get_words(self):
        """
        Get the list of NUM_WORDS_PER_SESSION random words selected for this session.
        Returns: A list of NUM_WORDS_PER_SESSION words (or fewer if not enough words available)
        """
        return self.word_list
    
    def record_word_result(self, user_input, correct_word_obj, similarity_score):
        """
        Record the result when the user submits an answer for a word.
        This stores what the user entered, the correct word, and the similarity score.
        
        Parameters:
        user_input: The word entered by the user (string)
        correct_word_obj: The Word object containing the correct word
        similarity_score: The similarity score between user input and correct word (float, 0.0 to 1.0)
        """
        # Store what the user typed (normalize to lowercase for consistency)
        self.words_entered.append(user_input.lower().strip())
        
        # Store the correct word text (extract from Word object)
        self.correct_words.append(correct_word_obj.word.lower().strip())
        
        # Store the similarity score
        self.similarity_scores.append(similarity_score)
        
        # Debug: Print word result
        print(f"[DEBUG] GameSession.record_word_result(): Word {len(self.words_entered)} - "
              f"Correct: '{correct_word_obj.word}' (level {correct_word_obj.level}), "
              f"Typed: '{user_input}', Similarity: {similarity_score:.3f}")
    
    def save_records_to_user(self, user_obj):
        """
        Save all session records to a User object.
        This method iterates through all words that were attempted in this session
        and adds each one as a record to the user, then saves all records to CSV.
        
        Parameters:
        user_obj: A User object to save the records to
        """
        # Iterate through all words that were attempted in this session
        # We use len(game.words_entered) to know how many words were attempted
        for i in range(len(self.words_entered)):
            # Get the word object to access its level
            # The word_list contains Word objects, and the indices should match
            if i < len(self.word_list):
                word_obj = self.word_list[i]
                level = word_obj.level
            else:
                # Fallback if somehow we don't have a word object
                # This shouldn't happen, but it's good to be safe
                level = 1
            
            # Add this word attempt as a record to the user
            # We have all the information we need from the session
            user_obj.add_record(
                session_id=self.id,                    # Unique session identifier
                word_typed=self.words_entered[i],      # What the user typed
                correct_word=self.correct_words[i],    # The correct spelling
                level=level,                           # Difficulty level
                similarity_score=self.similarity_scores[i]  # How similar (0.0 to 1.0)
            )
        
        # Save all user records (including the new ones) to the CSV file
        user_obj.save_to_csv()
        print(f"[DEBUG] GameSession.save_records_to_user(): Saved {len(self.words_entered)} records to {user_obj.csv_filename}")
        
        # Debug: Print session summary
        print(f"[DEBUG] GameSession.save_records_to_user(): Session {self.id:.2f} summary:")
        for i in range(len(self.words_entered)):
            word_obj = self.word_list[i] if i < len(self.word_list) else None
            level = word_obj.level if word_obj else "?"
            print(f"[DEBUG]   Word {i+1}: '{self.correct_words[i]}' (level {level}), "
                  f"typed: '{self.words_entered[i]}', score: {self.similarity_scores[i]:.3f}")


class BlinkingCursor:
    """
    This class manages the blinking cursor that shows where text will appear.
    """
    
    def __init__(self, blink_time=500):
        """
        Create a new blinking cursor.
        blink_time: How many milliseconds between each blink (default 500ms = half a second)
        """
        self.visible = True  # Is the cursor currently showing?
        self.blink_time = blink_time  # Time between blinks
        self.last_toggle = 0  # When we last changed visibility
    
    def update(self, current_time):
        """
        Check if enough time has passed to toggle the cursor visibility.
        This should be called every frame in the game loop.
        current_time: Current time from pygame.time.get_ticks()
        """
        # If enough time has passed since last toggle, change visibility
        if current_time - self.last_toggle > self.blink_time:
            self.visible = not self.visible  # Switch between True and False
            self.last_toggle = current_time
    
    def reset(self, current_time):
        """
        Make the cursor visible again and reset the timer.
        This is useful when the user starts typing.
        current_time: Current time from pygame.time.get_ticks()
        """
        self.visible = True
        self.last_toggle = current_time





# ============================================================================
# GAME STATE - Create GameEngine and GameSession
# ============================================================================

# Create a GameEngine that loads words from the CSV file
# The GameEngine acts as the word bank - it loads all words from the file
game_engine = GameEngine(WORD_BANK_CSV_FILENAME)

# The game can be in four screen states:
# - "NAME_INPUT": Screen to enter user name (first screen shown)
# - "START_MENU": Initial screen with button to start new session
# - "PLAYING": User is actively spelling words in a session
# - "END_SCREEN": Session complete, showing results
screen_state = "NAME_INPUT"

# Create a GameSession that selects NUM_WORDS_PER_SESSION random words for practice
# The GameSession tracks the current practice session
# We start with None - a session will be created when user clicks "Start Session"
game = None

# Create a blinking cursor object (cursor will blink every 500 milliseconds)
cursor = BlinkingCursor(blink_time=500)

# User object to track spelling practice records
# We start with None - the user will be created when they enter their name
current_user = None

# Store the name being typed on the name input screen
name_input = ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def draw_text_centered(text, font, color, y_position):
    """Draw text centered horizontally at a given y position"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, y_position))
    screen.blit(text_surface, text_rect)


def compare_words(correct, user_answer):
    """
    Compare the correct word with user's answer.
    Returns a list of booleans indicating which characters are correct.
    """
    differences = []
    max_length = max(len(correct), len(user_answer))

    for i in range(max_length):
        if i < len(correct) and i < len(user_answer):
            # Both words have a character at this position
            differences.append(correct[i] == user_answer[i])
        else:
            # One word is longer than the other
            differences.append(False)

    return differences


def draw_highlighted_word(correct_word, user_word, y_position):
    """
    Draw the correct word with user's mistakes highlighted.
    Green for correct letters, red for incorrect ones.
    """
    differences = compare_words(correct_word, user_word)

    # Calculate starting x position to center the word
    char_width = input_font.size("M")[0]  # Approximate character width
    total_width = char_width * len(correct_word)
    x_position = (WINDOW_WIDTH - total_width) // 2

    # Draw each character with appropriate color
    for i, char in enumerate(correct_word):
        if i < len(user_word):
            color = CORRECT_COLOR if differences[i] else ERROR_COLOR
        else:
            color = ERROR_COLOR  # Missing characters are errors

        char_surface = input_font.render(char, True, color)
        screen.blit(char_surface, (x_position + i * char_width, y_position))

    # Show if user typed extra characters
    if len(user_word) > len(correct_word):
        extra_text = message_font.render("(extra characters typed)", True, ERROR_COLOR)
        extra_rect = extra_text.get_rect(center=(WINDOW_WIDTH // 2, y_position + 60))
        screen.blit(extra_text, extra_rect)


def play_word(word_obj):
    """
    Play the word using the text-to-speech engine.
    word_obj: A Word object containing the word to play
    """
    # Extract the word text from the Word object and say it using the text-to-speech engine
    engine.say(word_obj.word)
    # Wait for the word to be spoken.
    engine.runAndWait()


def move_to_next_word(game_session_obj, cursor_obj):
    """
    Load the next word in the session's word list.
    This function takes the game session object and updates it with the next word.
    The word_list contains Word objects instead of strings.
    
    Returns True if there are more words, False if session is complete.
    """
    # Get the word list from the session
    word_list = game_session_obj.get_words()
    
    # Only proceed if we have words available
    if word_list:
        # Move to the next word (don't wrap around - we want to finish the session)
        game_session_obj.word_index += 1
        
        # Check if we've completed all words in the session
        if game_session_obj.word_index >= len(word_list):
            # Session is complete!
            print(f"[DEBUG] move_to_next_word(): Session complete! All {len(word_list)} words finished")
            return False
        
        # Load the next word
        game_session_obj.current_word = word_list[game_session_obj.word_index]
        game_session_obj.user_input = ""  # Clear what the user typed
        game_session_obj.state = "INPUT"  # Go back to input mode

        # Reset cursor to visible state when moving to next word
        cursor_obj.reset(pygame.time.get_ticks())

        # Debug: Print word progression
        if game_session_obj.current_word:
            print(f"[DEBUG] move_to_next_word(): Moving to word {game_session_obj.word_index + 1}/{len(word_list)}: "
                  f"'{game_session_obj.current_word.word}' (level {game_session_obj.current_word.level})")

        # Play the word audio
        play_word(game_session_obj.current_word)
        
        return True  # More words remaining
    
    # No words available
    return False


# ============================================================================
# MAIN GAME LOOP
# ============================================================================

running = True
while running:
    # Update cursor blinking - call the cursor's update method
    # This checks if enough time has passed and toggles visibility if needed
    current_time = pygame.time.get_ticks()
    cursor.update(current_time)

    # ========================================================================
    # EVENT HANDLING - Process user input
    # ========================================================================

    for event in pygame.event.get():
        # Window close button clicked
        if event.type == pygame.QUIT:
            running = False

        # Mouse button clicked
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if screen_state == "START_MENU":
                # Check if "Start Session" button was clicked
                start_button_rect = pygame.Rect(250, 300, 300, 80)
                if start_button_rect.collidepoint(mouse_pos):
                    # Create a new game session with words selected based on user history
                    # Pass current_user to enable personalized word selection
                    print(f"[DEBUG] Main loop: 'Start Session' button clicked")
                    game = game_engine.create_session(current_user)
                    screen_state = "PLAYING"
                    # Auto-play the first word
                    if game.current_word:
                        print(f"[DEBUG] Main loop: Auto-playing first word: '{game.current_word.word}'")
                        play_word(game.current_word)
            
            elif screen_state == "END_SCREEN":
                # Check if "New Session" button was clicked
                new_session_button_rect = pygame.Rect(140, 480, 240, 80)
                if new_session_button_rect.collidepoint(mouse_pos):
                    # Create a new game session with words selected based on user history
                    # Pass current_user to enable personalized word selection
                    print(f"[DEBUG] Main loop: 'New Session' button clicked")
                    game = game_engine.create_session(current_user)
                    screen_state = "PLAYING"
                    # Auto-play the first word
                    if game.current_word:
                        print(f"[DEBUG] Main loop: Auto-playing first word: '{game.current_word.word}'")
                        play_word(game.current_word)
                
                # Check if "Exit" button was clicked
                exit_button_rect = pygame.Rect(420, 480, 240, 80)
                if exit_button_rect.collidepoint(mouse_pos):
                    # User wants to exit the application
                    print(f"[DEBUG] Main loop: 'Exit' button clicked")
                    running = False
            
            elif screen_state == "PLAYING" and game.state == "INPUT":
                # Check if play button was clicked
                play_button_rect = pygame.Rect(300, 200, 200, 60)
                if play_button_rect.collidepoint(mouse_pos):
                    # Only play if we have a current word
                    if game.current_word:
                        play_word(game.current_word)

        # Key pressed
        elif event.type == pygame.KEYDOWN:
            if screen_state == "NAME_INPUT":
                # User is entering their name
                if event.key == pygame.K_RETURN:
                    # Enter key: Submit the name and load/create the user
                    if name_input.strip():  # Only proceed if name is not empty
                        # Create the User object (this will load existing records or create a new file)
                        print(f"[DEBUG] Main loop: Creating user with name '{name_input.strip()}'")
                        current_user = User(name=name_input.strip(), users_directory=USERS_DIRECTORY)
                        # Move to the start menu
                        screen_state = "START_MENU"
                        # Clear the name input
                        name_input = ""
                        print(f"[DEBUG] Main loop: User created, moved to START_MENU screen")
                
                elif event.key == pygame.K_BACKSPACE:
                    # Delete last character from name input
                    name_input = name_input[:-1]
                    # Show cursor immediately after deleting
                    cursor.reset(current_time)
                
                else:
                    # Only allow alphanumeric characters and spaces
                    # Check if the character is alphanumeric or a space
                    if event.unicode and (event.unicode.isalnum() or event.unicode == ' '):
                        name_input += event.unicode
                        # Show cursor immediately after typing
                        cursor.reset(current_time)
            
            elif screen_state == "PLAYING":
                if game.state == "INPUT":
                    # User is typing their answer
                    if event.key == pygame.K_RETURN:
                        # Enter key: Check the answer
                        if game.user_input and game.current_word:  # Only check if something was typed and we have a word
                            # Calculate similarity score using the Word object's compare method
                            # This gives us a score from 0.0 (completely different) to 1.0 (identical)
                            similarity_score = game.current_word.compare(game.user_input)
                            
                            # Compare user's input with the correct word (case-insensitive)
                            # Access the .word attribute from the Word object
                            game.is_correct = game.user_input.lower() == game.current_word.word.lower()
                            
                            # Debug: Print answer submission
                            print(f"[DEBUG] Main loop: Answer submitted - Word: '{game.current_word.word}' (level {game.current_word.level}), "
                                  f"Typed: '{game.user_input}', Similarity: {similarity_score:.3f}, Correct: {game.is_correct}")
                            
                            # Record this word result in the session
                            # This stores: what user entered, correct word, and similarity score
                            game.record_word_result(game.user_input, game.current_word, similarity_score)
                            
                            game.state = "FEEDBACK"  # Switch to feedback mode

                    elif event.key == pygame.K_BACKSPACE:
                        # Delete last character from user's input
                        game.user_input = game.user_input[:-1]
                        # Show cursor immediately after deleting
                        cursor.reset(current_time)

                    else:
                        # Add character to input (letters only)
                        if event.unicode.isalpha():
                            game.user_input += event.unicode
                            # Show cursor immediately after typing
                            cursor.reset(current_time)

                elif game.state == "FEEDBACK":
                    # User is viewing feedback, press any key to continue
                    has_more_words = move_to_next_word(game, cursor)
                    
                    # Check if session is complete
                    if not has_more_words:
                        # All words completed! Switch to end screen
                        print(f"[DEBUG] Main loop: Session complete, switching to END_SCREEN")
                        screen_state = "END_SCREEN"
                        
                        # Save all session records to the user's CSV file
                        # The GameSession class handles iterating through words and saving records
                        # Only save if we have a user (should always be the case, but check for safety)
                        if current_user:
                            game.save_records_to_user(current_user)
                        else:
                            print(f"[DEBUG] Main loop: Warning - No user object to save records to!")

    # ========================================================================
    # DRAWING - Render everything on screen
    # ========================================================================

    # Clear screen with background color
    screen.fill(BACKGROUND_COLOR)

    # Draw title
    draw_text_centered("BeeWise", title_font, ACCENT_COLOR, 60)

    if screen_state == "NAME_INPUT":
        # ====================================================================
        # NAME INPUT SCREEN - Ask user to enter their name
        # ====================================================================
        
        welcome_text = "Welcome to BeeWise!"
        draw_text_centered(welcome_text, message_font, TEXT_COLOR, 180)
        
        instruction_text = "Enter your name to begin"
        draw_text_centered(instruction_text, message_font, TEXT_COLOR, 230)
        
        # Draw input box with thick black border (neo-brutalism style)
        input_box_rect = pygame.Rect(200, 300, 400, 60)
        pygame.draw.rect(screen, INPUT_BOX_COLOR, input_box_rect)
        pygame.draw.rect(screen, BORDER_COLOR, input_box_rect, 5)  # Thick black border
        
        # Draw user's name input
        if name_input:
            name_surface = input_font.render(name_input, True, TEXT_COLOR)
            name_rect = name_surface.get_rect(center=(WINDOW_WIDTH // 2, 330))
            screen.blit(name_surface, name_rect)
            
            # Draw cursor after the text (only if cursor is visible)
            if cursor.visible:
                cursor_x = name_rect.right + 2
                cursor_y_top = name_rect.top
                cursor_y_bottom = name_rect.bottom
                pygame.draw.line(
                    screen,
                    TEXT_COLOR,
                    (cursor_x, cursor_y_top),
                    (cursor_x, cursor_y_bottom),
                    3,  # Thicker cursor for neo-brutalism
                )
        else:
            # Draw cursor at center when no text (only if cursor is visible)
            if cursor.visible:
                cursor_x = WINDOW_WIDTH // 2
                cursor_y_top = 330 - input_font.get_height() // 2
                cursor_y_bottom = 330 + input_font.get_height() // 2
                pygame.draw.line(
                    screen,
                    TEXT_COLOR,
                    (cursor_x, cursor_y_top),
                    (cursor_x, cursor_y_bottom),
                    3,  # Thicker cursor for neo-brutalism
                )
        
        # Instructions
        help_text = "Type your name and press ENTER (letters, numbers, and spaces only)"
        draw_text_centered(help_text, message_font, TEXT_COLOR, 410)
    
    elif screen_state == "START_MENU":
        # ====================================================================
        # START MENU - Initial screen with button to begin
        # ====================================================================
        
        welcome_text = "Welcome to BeeWise!"
        draw_text_centered(welcome_text, message_font, TEXT_COLOR, 180)
        
        instruction_text = "Practice your spelling skills"
        draw_text_centered(instruction_text, message_font, TEXT_COLOR, 230)
        
        # Start Session button with thick black border
        start_button_rect = pygame.Rect(250, 300, 300, 80)
        pygame.draw.rect(screen, PRIMARY_COLOR, start_button_rect)
        pygame.draw.rect(screen, BORDER_COLOR, start_button_rect, 4)  # Thick black border
        start_button_text = button_font.render("Start Session", True, TEXT_COLOR)
        start_button_text_rect = start_button_text.get_rect(
            center=start_button_rect.center
        )
        screen.blit(start_button_text, start_button_text_rect)
        
    elif screen_state == "END_SCREEN":
        # ====================================================================
        # END SCREEN - Session complete, show results
        # ====================================================================
        
        # Only proceed if we have a game session with results
        if game:
            # Calculate statistics from the session results
            num_total = len(game.words_entered)
            num_correct = 0
            incorrect_words = []
            
            # Count correct words and collect incorrect ones
            for i in range(num_total):
                # A word is correct if similarity score is 1.0 (perfect match)
                if i < len(game.similarity_scores) and game.similarity_scores[i] >= 1.0:
                    num_correct += 1
                else:
                    # Collect incorrect words - show what user typed and correct spelling
                    if i < len(game.correct_words):
                        incorrect_words.append((game.words_entered[i], game.correct_words[i]))
            
            # "Great work!" message
            draw_text_centered("Great work!", word_font, CORRECT_COLOR, 140)
            
            # Show number of correct words
            stats_text = f"You got {num_correct} out of {num_total} words correct!"
            draw_text_centered(stats_text, message_font, TEXT_COLOR, 210)
            
            # Show incorrect words if any
            if incorrect_words:
                draw_text_centered("Incorrect words:", message_font, TEXT_COLOR, 270)
                
                # Display each incorrect word (limit to fit on screen)
                start_y = 310
                line_height = 35
                max_words_to_show = 4  # Show up to 4 incorrect words to fit on screen
                
                for i, (user_word, correct_word) in enumerate(incorrect_words[:max_words_to_show]):
                    y_pos = start_y + (i * line_height)
                    # Show user_word in ERROR_COLOR and correct_word in CORRECT_COLOR
                    # Render each part separately to color them differently
                    user_surface = message_font.render(user_word, True, ERROR_COLOR)
                    arrow_surface = message_font.render(" -> ", True, TEXT_COLOR)
                    correct_surface = message_font.render(correct_word, True, CORRECT_COLOR)
                    
                    # Calculate total width to center the entire group horizontally
                    combined_width = user_surface.get_width() + arrow_surface.get_width() + correct_surface.get_width()
                    start_x = (WINDOW_WIDTH - combined_width) // 2
                    
                    # Calculate x positions for each part
                    user_x = start_x
                    arrow_x = start_x + user_surface.get_width()
                    correct_x = arrow_x + arrow_surface.get_width()
                    
                    # Get y position for vertical centering (blit uses top-left, so adjust by half height)
                    text_height = user_surface.get_height()
                    text_y = y_pos - text_height // 2
                    
                    # Draw each part in sequence
                    screen.blit(user_surface, (user_x, text_y))
                    screen.blit(arrow_surface, (arrow_x, text_y))
                    screen.blit(correct_surface, (correct_x, text_y))
                
                # If there are more incorrect words, indicate that
                if len(incorrect_words) > max_words_to_show:
                    more_text = f"... and {len(incorrect_words) - max_words_to_show} more"
                    draw_text_centered(more_text, message_font, TEXT_COLOR, start_y + (max_words_to_show * line_height))
            else:
                # All words correct!
                perfect_text = "Perfect! All words correct!"
                draw_text_centered(perfect_text, message_font, CORRECT_COLOR, 270)
        else:
            # Fallback if game is None
            draw_text_centered("Great work!", word_font, CORRECT_COLOR, 140)
            draw_text_centered("Session complete!", message_font, TEXT_COLOR, 210)
        
        # New Session button with thick black border (left side)
        new_session_button_rect = pygame.Rect(140, 480, 240, 80)
        pygame.draw.rect(screen, PRIMARY_COLOR, new_session_button_rect)
        pygame.draw.rect(screen, BORDER_COLOR, new_session_button_rect, 4)  # Thick black border
        new_session_button_text = button_font.render("New Session", True, TEXT_COLOR)
        new_session_button_text_rect = new_session_button_text.get_rect(
            center=new_session_button_rect.center
        )
        screen.blit(new_session_button_text, new_session_button_text_rect)
        
        # Exit button with thick black border (right side)
        exit_button_rect = pygame.Rect(420, 480, 240, 80)
        pygame.draw.rect(screen, ERROR_COLOR, exit_button_rect)
        pygame.draw.rect(screen, BORDER_COLOR, exit_button_rect, 4)  # Thick black border
        exit_button_text = button_font.render("Exit", True, TEXT_COLOR)
        exit_button_text_rect = exit_button_text.get_rect(
            center=exit_button_rect.center
        )
        screen.blit(exit_button_text, exit_button_text_rect)
        
    elif screen_state == "PLAYING" and game.state == "INPUT":
        # ====================================================================
        # INPUT STATE - User is typing
        # ====================================================================

        prompt_text = "Listen and spell the word"
        draw_text_centered(prompt_text, message_font, TEXT_COLOR, 160)

        # Play word button with thick black border
        play_button_rect = pygame.Rect(300, 200, 200, 60)
        pygame.draw.rect(screen, PRIMARY_COLOR, play_button_rect)
        pygame.draw.rect(screen, BORDER_COLOR, play_button_rect, 4)  # Thick black border
        play_button_text = button_font.render("Play Word", True, TEXT_COLOR)
        play_button_text_rect = play_button_text.get_rect(
            center=play_button_rect.center
        )
        screen.blit(play_button_text, play_button_text_rect)

        # Draw input box with thick black border (neo-brutalism style)
        input_box_rect = pygame.Rect(200, 300, 400, 60)
        pygame.draw.rect(screen, INPUT_BOX_COLOR, input_box_rect)
        pygame.draw.rect(screen, BORDER_COLOR, input_box_rect, 5)  # Thick black border

        # Draw user's input
        if game.user_input:
            input_surface = input_font.render(game.user_input, True, TEXT_COLOR)
            input_rect = input_surface.get_rect(center=(WINDOW_WIDTH // 2, 330))
            screen.blit(input_surface, input_rect)

            # Draw cursor after the text (only if cursor is visible)
            if cursor.visible:
                cursor_x = input_rect.right + 2
                cursor_y_top = input_rect.top
                cursor_y_bottom = input_rect.bottom
                pygame.draw.line(
                    screen,
                    TEXT_COLOR,
                    (cursor_x, cursor_y_top),
                    (cursor_x, cursor_y_bottom),
                    3,  # Thicker cursor for neo-brutalism
                )
        else:
            # Draw cursor at center when no text (only if cursor is visible)
            if cursor.visible:
                cursor_x = WINDOW_WIDTH // 2
                cursor_y_top = 330 - input_font.get_height() // 2
                cursor_y_bottom = 330 + input_font.get_height() // 2
                pygame.draw.line(
                    screen,
                    TEXT_COLOR,
                    (cursor_x, cursor_y_top),
                    (cursor_x, cursor_y_bottom),
                    3,  # Thicker cursor for neo-brutalism
                )

        # Instructions
        instruction_text = "Type your answer and press ENTER"
        draw_text_centered(instruction_text, message_font, TEXT_COLOR, 410)

    elif screen_state == "PLAYING" and game.state == "FEEDBACK":
        # ====================================================================
        # FEEDBACK STATE - Showing results
        # ====================================================================

        if game.is_correct and game.current_word:
            # Correct answer!
            draw_text_centered("Excellent!", word_font, CORRECT_COLOR, 180)
            # Access the .word attribute from the Word object to display the word text
            draw_text_centered(
                f"'{game.current_word.word}' is correct!", message_font, TEXT_COLOR, 260
            )

        else:
            # Incorrect answer
            draw_text_centered("Not quite right", word_font, ERROR_COLOR, 160)

            # Show what user typed
            user_label = message_font.render("You typed:", True, TEXT_COLOR)
            user_label_rect = user_label.get_rect(center=(WINDOW_WIDTH // 2, 240))
            screen.blit(user_label, user_label_rect)

            user_surface = input_font.render(game.user_input, True, ERROR_COLOR)
            user_rect = user_surface.get_rect(center=(WINDOW_WIDTH // 2, 290))
            screen.blit(user_surface, user_rect)

            # Show correct spelling with highlighting
            correct_label = message_font.render("Correct spelling:", True, TEXT_COLOR)
            correct_label_rect = correct_label.get_rect(center=(WINDOW_WIDTH // 2, 360))
            screen.blit(correct_label, correct_label_rect)

            # Access the .word attribute from the Word object to get the word text for highlighting
            if game.current_word:
                draw_highlighted_word(game.current_word.word, game.user_input, 410)

        # Continue instruction
        continue_text = "Press any key for next word"
        draw_text_centered(continue_text, message_font, PRIMARY_COLOR, 520)

    # Progress indicator - shows which word we're on (only during PLAYING state)
    if screen_state == "PLAYING" and game:
        session_words = game.get_words()
        progress_text = f"Word {game.word_index + 1} of {len(session_words)}"
        progress_surface = message_font.render(progress_text, True, TEXT_COLOR)
        screen.blit(progress_surface, (20, WINDOW_HEIGHT - 40))

    # ========================================================================
    # UPDATE DISPLAY
    # ========================================================================

    pygame.display.flip()
    clock.tick(60)  # 60 frames per second

# ============================================================================
# CLEANUP
# ============================================================================

pygame.quit()
sys.exit()
