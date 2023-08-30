# alvin-seeker

Alvin DCIMGSeeker 1.0.2
30.08.2023
By Loke Sjølie, University of Oslo

This script takes a json dict as input. Each object in the json dict should have a representative name, and it should contain Alvin IDs.
The IDs are stringified by the script.
{
  "COLLECTION_ID_1": [
     000000,000001,000002
  ],
  "COLLECTION_ID_2": [
     000000,000001,000002
  ]
}

Versatile OAI-PMH protocol fetching Dublin Core from specified Alvin record(s). Also fetches image links from the supposed RDF OAI endpoint.
The links are used to communicate with the IIP server for direct image links. The images are then all downloaded locally.
