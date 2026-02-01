from django.db import models

class Election(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    contract_address = models.CharField(max_length=42, unique=True)

    def __str__(self):
        return self.name


class Voter(models.Model):
    wallet_address = models.CharField(max_length=42)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('wallet_address', 'election')

    def __str__(self):
        return f"{self.wallet_address} - {self.election.name}"


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} ({self.election.name})"
