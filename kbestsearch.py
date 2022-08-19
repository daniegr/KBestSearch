import random
import math

def print_status(candidate_string, performance, candidate_num, best, best_performance, best_candidate_num, population, temperature=None, unsuccessful_trials=None):
    print('###############################################')
    
    # Results of current candidate
    print('Candidate {0} {1} had performance {2:.5f}.'.format(candidate_num, candidate_string, performance))
    
    # Current best candidate
    print('\nThe best trial is candidate {0} {1} with performance {2:.5f}.'.format(best_candidate_num, best, best_performance))
    
    # Current population
    if len(population) > 0:
        print('\nThe population is:')
        for n in range(1, len(population)+1):
            candidate_string, performance, candidate_num = population[-n]
            print(' {0}. Candidate {1} {2} with performance {3:.5f}.'.format(n, candidate_num, candidate_string, performance))
            
    # Current temperature and number of unsuccessful trials at this temperature
    if not temperature is None:
        print('\nThe temperature is {0} with {1} unsuccessful trials'.format(temperature, unsuccessful_trials))
   
    print('###############################################\n\n')
    
def update_best(candidate_string, performance, candidate_num, best, best_performance, best_candidate_num):
    
    # Compare to best candidate
    if performance > best_performance:
        best_performance = performance
        best_candidate_num = candidate_num
        best = candidate_string
    
    return best, best_performance, best_candidate_num

def get_candidate(search_space, candidate_history):
    
    # Define max attempts as twice the number of unique candidates
    max_attempts = 2
    for choice in search_space.keys():
        max_attempts *= len(list(search_space[choice].keys()))
    
    # Fetch candidate
    attempt = 1
    while max_attempts >= attempt:
    
        # Initialize candidate
        candidate = {}
        candidate_string = ''

        # Iterate over choices
        for choice in search_space.keys():

            # Select alternatives based on probability in search space
            random_number = random.uniform(0, 1)
            alternatives = search_space[choice].keys()
            value = 0.0
            for alternative in alternatives:
                alternative_prob = search_space[choice][alternative]
                value += alternative_prob
                if value >= random_number:
                    candidate[choice] = alternative
                    candidate_string += '_{0}-{1}'.format(choice, alternative) if len(candidate_string) > 1 else '{0}-{1}'.format(choice, alternative)
                    break

        if candidate_string not in candidate_history:
            candidate_history.append(candidate_string)
            break
        else:
            attempt += 1
            if attempt > max_attempts:
                candidate = None
                candidate_string = ''
    
    return candidate, candidate_string, candidate_history  

def update_search_space(population, temperature):
    
    # Determine contribution of each alternative in search space
    search_space_count = {}
    for n, (candidate_string, _, _) in enumerate(population, 1):
        structure = candidate_string.split('_')
        for pair in structure:
            choice, alternative = pair.split('-')
            if not choice in search_space_count.keys():
                search_space_count[choice] = {}
            try:
                search_space_count[choice][alternative] += n
            except:
                search_space_count[choice][alternative] = n
                                    
    # Compute search space probabilities based on softmax
    search_space = {}
    for choice in search_space_count.keys():
        exp_sum = 0.0
        for alternative in search_space_count[choice].keys():
            exp_sum += math.exp(search_space_count[choice][alternative]/temperature)
        search_space[choice] = {}
        for alternative in search_space_count[choice].keys():
            search_space[choice][alternative] = math.exp(search_space_count[choice][alternative]/temperature) / exp_sum
                
    return search_space

def search(search_space, trainval, k = 5, start_temperature = 10, end_temperature = 1, temperature_drop = 3, performance_threshold = 0.9):
    
    # Initialize search history
    candidate_history = []
    best_performance = 0.0
    best_candidate_num = None
    best = None
    
    # Initialize search space with uniform probabilities
    for choice in search_space.keys():
        alternatives = search_space[choice]
        num_alternatives = len(alternatives)
        search_space[choice] = {}
        for alternative in alternatives:
            search_space[choice][alternative] = 1/num_alternatives
    
    # Obtain initial population with random search
    random_search = True
    random_candidate_num = 1
    population = []
    while len(population) < k:

        # Fetch unexplored candidate
        candidate, candidate_string, candidate_history = get_candidate(search_space, candidate_history)
        if candidate is None:
            break

        # Perform training and validation
        performance = trainval(candidate)

        # Keep track of best candidate
        best, best_performance, best_candidate_num = update_best(candidate_string, performance, 'r{0}'.format(random_candidate_num), best, best_performance, best_candidate_num)

        # Include in population if meets performance requirement
        if performance >= performance_threshold:
            population.append((candidate_string, performance, 'r' + str(random_candidate_num)))
            population = sorted(population, key=lambda x: x[1])
        
        # Print search status
        print_status(candidate_string, performance, 'r{0}'.format(random_candidate_num), best, best_performance, best_candidate_num, population)

        random_candidate_num += 1

    # Update population with search for K best candidates
    if len(population) == k:
            
        # Sort population on performance
        population = sorted(population, key=lambda x: x[1])

        # Initialize temperature
        temperature = start_temperature

        # Update search space from candidates in population  
        search_space = update_search_space(population, temperature=temperature)

        # Perform search
        candidate_num = 1
        unsuccessful_trials = 0
        while True:

            # Fetch unexplored candidate
            candidate, candidate_string, candidate_history = get_candidate(search_space, candidate_history)
            if candidate is None:
                break

            # Perform training and validation
            performance = trainval(candidate)

            # Keep track of best candidate
            best, best_performance, best_candidate_num = update_best(candidate_string, performance, candidate_num, best, best_performance, best_candidate_num)

            # Update population if improves upon lowest performing candidate in population
            if performance > population[0][1]:
                population[0] = (candidate_string, performance, candidate_num)
                population = sorted(population, key=lambda x: x[1])
                unsuccessful_trials = 0
            else:
                unsuccessful_trials += 1

            # Update search space probabilities from population
            search_space = update_search_space(population, temperature=temperature)

            # Decrease search temperature or terminate search if reached end temperature
            if unsuccessful_trials == k and temperature == end_temperature:
                print_status(candidate_string, performance, candidate_num, best, best_performance, best_candidate_num, population, temperature, unsuccessful_trials)
                break
            elif unsuccessful_trials == k:
                temperature -= temperature_drop
                unsuccessful_trials = 0
                
            # Print search status
            print_status(candidate_string, performance, candidate_num, best, best_performance, best_candidate_num, population, temperature, unsuccessful_trials)
                
            candidate_num += 1
                
if __name__ == '__main__':
    
    # Customize choices and associated alternatives in search space
    search_space = {
        'choice1': ['alt1', 'alt2', 'alt3'],
        'choice2': ['alt1', 'alt2', 'alt3', 'alt4'],
        'choice3': ['alt1', 'alt2']
    }
    
    # Customize trainval to perform training and validation of the provided candidate
    def trainval(candidate):
        performance = random.uniform(0,1)
        
        return performance
    
    # Perform K-Best Search
    search(search_space, trainval)