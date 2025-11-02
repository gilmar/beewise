"""
Simple test for word selection logic.

This test validates that the word selection algorithm works correctly.
Tests only the logic in the classes, not the UI.
Run with: python test_word_selection.py
"""

import os
import csv
import random
import tempfile
import shutil

class Word:
    def __init__(self, word, level, source):
        self.word = word.lower().strip()
        self.level = int(level)
        self.source = source.strip()

class User:
    def __init__(self, name, users_directory="users"):
        self.name = name.strip()
        self.records = []
        # Skip CSV loading for tests - we'll add records manually
        os.makedirs(users_directory, exist_ok=True)
    
    def add_record(self, session_id, word_typed, correct_word, level, similarity_score):
        record = {
            "session_id": session_id,
            "word_typed": word_typed.lower().strip(),
            "correct_word": correct_word.lower().strip(),
            "level": int(level),
            "similarity_score": float(similarity_score)
        }
        self.records.append(record)
    
    def get_level(self):
        if len(self.records) == 0:
            print(f"    [DEBUG] User '{self.name}' has no records, returning level 1")
            return 1
        level_counts = {}
        for record in self.records:
            if record['similarity_score'] >= 1.0:
                level = record['level']
                if level not in level_counts:
                    level_counts[level] = 0
                level_counts[level] += 1
        if len(level_counts) == 0:
            print(f"    [DEBUG] User '{self.name}' has no perfect scores, returning level 1")
            return 1
        max_level = 1
        max_count = 0
        for level in level_counts:
            count = level_counts[level]
            if count > max_count:
                max_count = count
                max_level = level
        print(f"    [DEBUG] User '{self.name}' level: {max_level} (perfect scores by level: {level_counts})")
        return max_level
    
    def get_mispelled_words_with_averages(self):
        word_scores = {}
        word_levels = {}
        for record in self.records:
            correct_word = record['correct_word']
            similarity_score = record['similarity_score']
            level = record['level']
            if correct_word not in word_scores:
                word_scores[correct_word] = []
                word_levels[correct_word] = level
            word_scores[correct_word].append(similarity_score)
        mispelled_words = []
        for correct_word in word_scores:
            scores_list = word_scores[correct_word]
            total_score = 0.0
            for score in scores_list:
                total_score += score
            average_score = total_score / len(scores_list)
            if average_score < 0.99:
                level = word_levels[correct_word]
                mispelled_words.append((correct_word, average_score, level))
        # Sort by average_score (ascending - worst first)
        temp_list = []
        for item in mispelled_words:
            correct_word = item[0]
            average_score = item[1]
            level = item[2]
            temp_list.append((average_score, correct_word, level))
        temp_list.sort()
        sorted_mispelled_words = []
        for item in temp_list:
            average_score = item[0]
            correct_word = item[1]
            level = item[2]
            sorted_mispelled_words.append((correct_word, average_score, level))
        return sorted_mispelled_words

class GameEngine:
    def __init__(self, csv_filename):
        self.all_words = []
        try:
            with open(csv_filename, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    word_text = row['word'].strip()
                    level = row['level'].strip()
                    source = row['source'].strip()
                    if word_text:
                        word_obj = Word(word_text, level, source)
                        self.all_words.append(word_obj)
        except FileNotFoundError:
            print(f"Error: Could not find file '{csv_filename}'")
            self.all_words = []
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            self.all_words = []
    
    def get_max_level(self):
        if len(self.all_words) == 0:
            return 1
        max_level = self.all_words[0].level
        for word_obj in self.all_words:
            if word_obj.level > max_level:
                max_level = word_obj.level
        return max_level
    
    def get_words_by_level(self, level):
        words_at_level = []
        for word_obj in self.all_words:
            if word_obj.level == level:
                words_at_level.append(word_obj)
        return words_at_level
    
    def create_session(self, user_obj=None, num_words_per_session=3):
        if user_obj is None or len(user_obj.records) == 0:
            # Use level 1 words only when no user or user has no records
            level_1_words = self.get_words_by_level(1)
            if len(level_1_words) >= num_words_per_session:
                selected = random.sample(level_1_words, num_words_per_session)
            else:
                selected = level_1_words.copy() if level_1_words else []
            return type('Session', (), {'word_list': selected})()
        
        words_per_category = num_words_per_session // 3
        remainder = num_words_per_session % 3
        selected_words = []
        user_level = user_obj.get_level()
        max_level = self.get_max_level()
        
        # Category 1: Mispelled words
        mispelled_list = user_obj.get_mispelled_words_with_averages()
        mispelled_word_objects = []
        for correct_word, avg_score, word_level in mispelled_list:
            for word_obj in self.all_words:
                if word_obj.word == correct_word:
                    mispelled_word_objects.append(word_obj)
                    break
        
        num_from_mispelled = words_per_category
        if remainder > 0:
            num_from_mispelled += 1
            remainder -= 1
        
        if len(mispelled_word_objects) >= num_from_mispelled:
            selected_words.extend(mispelled_word_objects[:num_from_mispelled])
        else:
            selected_words.extend(mispelled_word_objects)
        
        # Category 2: One level above
        target_level = user_level + 1
        if target_level > max_level:
            target_level = max_level
        
        words_at_target_level = self.get_words_by_level(target_level)
        available_at_target = []
        for word_obj in words_at_target_level:
            already_selected = False
            for selected_word_obj in selected_words:
                if selected_word_obj.word == word_obj.word:
                    already_selected = True
                    break
            if not already_selected:
                available_at_target.append(word_obj)
        
        num_from_higher = words_per_category
        if remainder > 0:
            num_from_higher += 1
            remainder -= 1
        
        if len(available_at_target) >= num_from_higher:
            selected_words.extend(random.sample(available_at_target, num_from_higher))
        else:
            selected_words.extend(available_at_target)
        
        # Category 3: Same level
        words_at_user_level = self.get_words_by_level(user_level)
        available_at_user_level = []
        for word_obj in words_at_user_level:
            already_selected = False
            for selected_word_obj in selected_words:
                if selected_word_obj.word == word_obj.word:
                    already_selected = True
                    break
            if not already_selected:
                available_at_user_level.append(word_obj)
        
        num_needed = num_words_per_session - len(selected_words)
        if num_needed > 0 and len(available_at_user_level) > 0:
            if len(available_at_user_level) >= num_needed:
                selected_words.extend(random.sample(available_at_user_level, num_needed))
            else:
                selected_words.extend(available_at_user_level)
        
        # Fill remaining if needed
        if len(selected_words) < num_words_per_session:
            remaining_words = []
            for word_obj in self.all_words:
                already_selected = False
                for selected_word_obj in selected_words:
                    if selected_word_obj.word == word_obj.word:
                        already_selected = True
                        break
                if not already_selected:
                    remaining_words.append(word_obj)
            still_needed = num_words_per_session - len(selected_words)
            if len(remaining_words) >= still_needed:
                selected_words.extend(random.sample(remaining_words, still_needed))
            else:
                selected_words.extend(remaining_words)
        
        random.shuffle(selected_words)
        return type('Session', (), {'word_list': selected_words})()


# ============================================================================
# TESTS
# ============================================================================

def test_mispelled_words_calculation():
    """Test that mispelled words are correctly identified."""
    print("Test 1: Mispelled words calculation...")
    
    test_dir = tempfile.mkdtemp()
    try:
        user = User("TestUser", users_directory=test_dir)
        
        # Add records: word "python" was misspelled (scores 0.5, 0.6, 0.7)
        user.add_record(1000.0, "pithon", "python", 1, 0.5)
        user.add_record(1001.0, "pythin", "python", 1, 0.6)
        user.add_record(1002.0, "pythan", "python", 1, 0.7)
        # Average = (0.5 + 0.6 + 0.7) / 3 = 0.6 (mispelled)
        
        # Add record: word "apple" was perfect (score 1.0)
        user.add_record(1003.0, "apple", "apple", 1, 1.0)
        
        mispelled = user.get_mispelled_words_with_averages()
        
        assert len(mispelled) == 1, f"Expected 1 mispelled word, got {len(mispelled)}"
        word, avg_score, level = mispelled[0]
        assert word == "python", f"Expected 'python', got '{word}'"
        assert abs(avg_score - 0.6) < 0.01, f"Expected average ~0.6, got {avg_score}"
        print("  ✓ PASSED")
    finally:
        shutil.rmtree(test_dir)


def test_mispelled_words_sorted():
    """Test that mispelled words are sorted worst first."""
    print("Test 2: Mispelled words sorting...")
    
    test_dir = tempfile.mkdtemp()
    try:
        user = User("TestUser", users_directory=test_dir)
        
        # Add three words with different average scores
        user.add_record(1000.0, "badd", "bad", 1, 0.2)
        user.add_record(1001.0, "baddd", "bad", 1, 0.4)  # Average 0.3
        
        user.add_record(1002.0, "okayy", "okay", 1, 0.6)  # Average 0.6
        
        user.add_record(1003.0, "goodd", "good", 1, 0.8)  # Average 0.8
        
        mispelled = user.get_mispelled_words_with_averages()
        
        assert len(mispelled) == 3, f"Expected 3 mispelled words, got {len(mispelled)}"
        assert mispelled[0][0] == "bad", "Worst word should be first"
        assert mispelled[1][0] == "okay", "Medium word should be second"
        assert mispelled[2][0] == "good", "Best mispelled word should be last"
        print("  ✓ PASSED")
    finally:
        shutil.rmtree(test_dir)


def test_word_selection_three_categories():
    """Test that word selection includes all three categories."""
    print("Test 3: Word selection three categories...")
    
    test_dir = tempfile.mkdtemp()
    try:
        # Create test CSV
        test_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        test_csv.write("word,level,source\n")
        for i in range(5):
            test_csv.write(f"word1_{i},1,test\n")
        for i in range(5):
            test_csv.write(f"word2_{i},2,test\n")
        for i in range(5):
            test_csv.write(f"word3_{i},3,test\n")
        test_csv.close()
        
        engine = GameEngine(test_csv.name)
        user = User("TestUser", users_directory=test_dir)
        user.add_record(1000.0, "word2_0", "word2_0", 2, 1.0)
        user.add_record(1001.0, "word1_0_bad", "word1_0", 1, 0.5)
        user.add_record(1002.0, "word1_0_bad2", "word1_0", 1, 0.6)
        
        session = engine.create_session(user_obj=user, num_words_per_session=3)
        
        assert len(session.word_list) == 3, f"Expected 3 words, got {len(session.word_list)}"
        
        # Check no duplicates
        word_texts = [w.word for w in session.word_list]
        assert len(word_texts) == len(set(word_texts)), "No duplicate words allowed"
        
        print("  ✓ PASSED")
        os.unlink(test_csv.name)
    finally:
        shutil.rmtree(test_dir)


def test_word_selection_user_at_max_level():
    """Test word selection when user is at max level."""
    print("Test 4: User at max level...")
    
    test_dir = tempfile.mkdtemp()
    try:
        test_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        test_csv.write("word,level,source\n")
        for level in [1, 2, 3, 4]:
            for i in range(5):
                test_csv.write(f"word{level}_{i},{level},test\n")
        test_csv.close()
        
        engine = GameEngine(test_csv.name)
        assert engine.get_max_level() == 4, "Max level should be 4"
        
        user = User("MaxUser", users_directory=test_dir)
        for i in range(5):
            user.add_record(1000.0 + i, f"word4_{i}", f"word4_{i}", 4, 1.0)
        
        session = engine.create_session(user_obj=user, num_words_per_session=3)
        
        # All words should be level 4 or lower
        for word_obj in session.word_list:
            assert word_obj.level <= 4, f"Word level {word_obj.level} exceeds max level 4"
        
        print("  ✓ PASSED")
        os.unlink(test_csv.name)
    finally:
        shutil.rmtree(test_dir)


def test_word_selection_no_user_level_1_only():
    """Test that when no user exists, only level 1 words are selected."""
    print("Test 5: No user - level 1 words only...")
    
    test_dir = tempfile.mkdtemp()
    try:
        test_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        test_csv.write("word,level,source\n")
        for i in range(5):
            test_csv.write(f"word1_{i},1,test\n")
        for i in range(5):
            test_csv.write(f"word2_{i},2,test\n")
        for i in range(5):
            test_csv.write(f"word3_{i},3,test\n")
        test_csv.close()
        
        engine = GameEngine(test_csv.name)
        
        # Test with no user (None)
        session = engine.create_session(user_obj=None, num_words_per_session=3)
        
        assert len(session.word_list) == 3, f"Expected 3 words, got {len(session.word_list)}"
        
        # All words should be level 1
        for word_obj in session.word_list:
            assert word_obj.level == 1, f"Expected level 1, got level {word_obj.level} for word '{word_obj.word}'"
        
        # Test with user that has no records
        user = User("NewUser", users_directory=test_dir)
        session2 = engine.create_session(user_obj=user, num_words_per_session=3)
        
        assert len(session2.word_list) == 3, f"Expected 3 words, got {len(session2.word_list)}"
        
        # All words should be level 1
        for word_obj in session2.word_list:
            assert word_obj.level == 1, f"Expected level 1, got level {word_obj.level} for word '{word_obj.word}'"
        
        print("  ✓ PASSED")
        os.unlink(test_csv.name)
    finally:
        shutil.rmtree(test_dir)


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("Testing Word Selection Logic")
    print("="*50 + "\n")
    
    try:
        test_mispelled_words_calculation()
        test_mispelled_words_sorted()
        test_word_selection_three_categories()
        test_word_selection_user_at_max_level()
        test_word_selection_no_user_level_1_only()
        
        print("\n" + "="*50)
        print("All tests PASSED! ✓")
        print("="*50 + "\n")
        return True
    except AssertionError as e:
        print(f"\n  ✗ FAILED: {e}")
        print("\n" + "="*50)
        print("Test FAILED!")
        print("="*50 + "\n")
        return False
    except Exception as e:
        print(f"\n  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    random.seed(42)  # For reproducible tests
    success = run_all_tests()
    exit(0 if success else 1)
