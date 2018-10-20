from rugbydb import RugbyDB, CachedDB
from datetime import datetime

from player import Player

class MatchList():
    """
    Class to store and manipulate Match objects
    """

    @classmethod
    def createMatchListForTeam(cls, teamName, leagues=None, seasons=None):
        """
        Create a match list for a specific team, filter by league or seasons
        ARGS:
            teamName (str) - name of the team
            leagues ([int]) - list of league ids to filter by, search all leagues if None
            seasons ([str]) - list of seasons to filter by, search all seasons if None
        RETURNS
            MatchList - MatchList object
        """
        db = CachedDB()
        matchIds = db.getMatchesForTeam(teamName.lower(), leagues=leagues, seasons=seasons)
        return cls(matchIds)

    @classmethod
    def createMatchListForLeague(cls, leagueId):
        pass

    def __init__(self, matchIds):
        """
        ARGS:
            matchIds [int] - list of match ids to load into the matchlist
        """
        self._matches = {}
        self._teams = None
        db = CachedDB()
        for id in matchIds:
            self._matches[id] = Match.fromMatchId(id)
    
    def __str__(self):
        """
        String representation of MatchList
        """
        return "{}".format(self._matches.keys())

    def __len__(self):
        """
        Len representation of MatchList
        """
        return len(self._matches.keys())

    def __add__(aMatchList, bMatchList):
        """
        Override add operator to add two matchlists together
        """
        for id in bMatchList._matches.keys():
            aMatchList.addMatch(id, bMatchList._matches[id])
        return aMatchList

    def getMatchIds(self):
        """
        Return all match ids in the MatchList
        RETURNS:
            [int] - list of match ids
        """
        return sorted(self._matches.keys())

    def getAllTeams(self):
        """
        Return list of teams that play in the MatchList
        RETURNS:
            [str] - list of team names
        """
        if self._teams is None:
            self._teams = []
            for match in self._matches.items():
                self._teams.append(match.homeTeam)
        return self._teams

    def __iter__(self):
        """
        Iterator implementation for MatchList
        """
        self.currentMatchIndex = -1
        return self

    def next(self):
        """
        Iterator implementation for MatchList
        RETURNS:
            Match (obj) - returns next match object in list
        """
        matchIds = self.getMatchIds()
        if self.currentMatchIndex >= len(matchIds) - 1:
            raise StopIteration
        else:
            self.currentMatchIndex += 1
            return self._matches[matchIds[self.currentMatchIndex]]
    
    def addMatch(self, id, match):
        """
        Add a new match to the matchlist
        ARGS:
            id (int) - match id of the new match
            match (Match) - match to add
        """
        self._matches[id] = match

    def getMatchesinDateRange(self, startDate=None, endDate=None):
        """
        Filter MatchList for a given date range, returns a new MatchList
        ARGS:
            startDate (datetime) - start date in range to search, default to datetime.min
            endDate (datetime) - end date in range to search, default to datetime.max
        RETURNS:
            MatchList (obj) - return new MatchList object with matches in date range
        """
        matches = MatchList(matchIds=[])
        if startDate is None:
            startDate = datetime.min
        if endDate is None:
            endDate = datetime.max
        for id in self._matches.keys():
            match = self._matches[id]
            if match.date > startDate and match.date < endDate:
                matches.addMatch(id, match)
        return matches


class MatchListLite(MatchList):
    """
    Lite version of MatchList which doesnt load all matches
    Used to store matchIds only and overrides functionality 
    that accessed Match object data
    """
    def __init__(self, matchIds):
        """
        ARGS:
            matchIds [int] - list of match ids to load into the matchlist
        """
        self._matches = {el: None for el in matchIds}

    def getAllTeams(self):
        """
        Returns an empty list as MatchListLite does not have access to Match data
        RETURNS:
            [] - empty list
        """
        return []

    def next(self):
        """
        Iterator implementation for MatchList
        RETURNS:
            int - returns next match id in list
        """
        matchIds = self.getMatchIds()
        if self.currentMatchIndex >= len(matchIds) - 1:
            raise StopIteration
        else:
            self.currentMatchIndex += 1
            return matchIds[self.currentMatchIndex]

    def getMatchesinDateRange(self, startDate=None, endDate=None):
        """
        Not implemented for MatchListLite
        ARGS:
            startDate (datetime) - start date in range to search
            endDate (datetime) - end date in range to search
        RETURNS:
            None - not implemented
        """
        return None


class Match():

    @classmethod
    def fromMatchId(cls, matchId):
        """
        Create a Match object from match id
        ARGS:
            matchId (int) - id for a match to create object for
        RETURNS
            Match (obj) - Match object
        """
        db = CachedDB()
        return cls(db.getMatchById(matchId))

    def __init__(self, matchDict):
        """
        ARGS:
            matchDict (dict) - dictionary storing match information from database
        """
        homeTeam = matchDict['gamePackage']['gameStrip']['teams']['home'] 
        awayTeam = matchDict['gamePackage']['gameStrip']['teams']['away']
        date = matchDict['gamePackage']['gameStrip']['isoDate']
        dataVis = matchDict['gamePackage']['matchStats']['dataVis']
        table = matchDict['gamePackage']['matchStats']['table']
        scores = matchDict['gamePackage']['matchEvents']['col'][0][0]['data']
        attacking = matchDict['gamePackage']['matchEvents']['col'][1][1]['data']
        discipline = matchDict['gamePackage']['matchDiscipline']['col'][1][0]['data']
        penalties = matchDict['gamePackage']['matchDiscipline']['col'][0][0]['data']
        players = matchDict['gamePackage']['matchLineUp']

        dateParts = date[:10].split('-')
        timeParts = date[11:-1].split(':')
        self.date = datetime(int(dateParts[0]),
                             int(dateParts[1]),
                             int(dateParts[2]),
                             int(timeParts[0]),
                             int(timeParts[1]))
        self.homeTeam = {'name': homeTeam['name'], 'abbrev': homeTeam['abbrev'], 'score': homeTeam['score']}
        self.awayTeam = {'name': awayTeam['name'], 'abbrev': awayTeam['abbrev'], 'score': awayTeam['score']}
        self.matchStats = {'Points': {'homeValue': float(homeTeam['score']), 'awayValue': float(awayTeam['score'])}}

        for item in dataVis + table + discipline + scores + attacking:
            try:
                homeValue = float(item['homeValue'])
                awayValue = float(item['awayValue'])
            except:
                homeValue = float(item['homeValue'][:-1])
                awayValue = float(item['awayValue'][:-1])
            self.matchStats[item['text']] = {'homeValue': homeValue, 'awayValue': awayValue}
        self.matchStats['Penalties Conceded'] = {'homeValue': float(penalties['homeTotal']), 'awayValue': float(penalties['awayTotal'])}
        self.players = {'home': [], 'away': []}
        for team in self.players.keys():
            for player in players[team]['team']:
                self.players[team].append(Player(player))
    
    def __str__(self):
        """
        String representation of a match
        """
        return "{} v {} - {}".format(self.homeTeam['name'], self.awayTeam['name'], self.date)

    def getAllStatHeaders(self):
        """
        Return all possibles stats for the match
        RETURNS:
            [str] - list of stat headers for the match
        """
        return self.matchStats.keys()

    def getHomeAwayValue(self, team):
        """
        Return homeValue or awayValue depending on whether the
        team is home or away
        ARGS:
            team (str) - team name
        RETURNS:
            str - homeValue/awayValue for the team or None if team is not in the match
        """
        if team.lower() == self.homeTeam['name'].lower():
            return 'homeValue'
        elif team.lower() == self.awayTeam['name'].lower():
            return 'awayValue'
        else:
            return None

    def getStatForTeam(self, team, stat):
        """
        Return a stats value for a given team if they played in the match
        ARGS:
            team (str) - team name
            stat (str) - stat name to get
        RETURNS:
            float - value for stat or None if not found
        """
        if stat in self.matchStats.keys():
            value = self.getHomeAwayValue(team)
            return self.matchStats[stat][value] if value is not None else None
        return None
