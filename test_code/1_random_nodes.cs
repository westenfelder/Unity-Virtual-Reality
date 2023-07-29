using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;

/*
 * TODO:
 * comment code, add the function headers
 * Move functions to different file
*/

public class Main : MonoBehaviour
{
    // Public objects, must be connected to assets in the main window
    public GameObject nodePrefab;
    public GameObject connectionPrefab;
    public Transform scaleObject;

    // Structure for a connection between two nodes
    struct Connection
    {
        public GameObject connectionObject;
        public GameObject node1Object;
        public GameObject node2Object;
        public int numPackets;
    }

    // List of connections and nodes
    private List<Connection> connectionList = new List<Connection>();
    private List<GameObject> nodeList = new List<GameObject>();

    // Create a node given position, rotation, and scale vectors
    GameObject createNode(Vector3 position, Vector3 rotation, Vector3 scale)
    {
        GameObject newNode = Instantiate(nodePrefab, position, Quaternion.Euler(rotation)) as GameObject;
        newNode.transform.localScale = scale;
        return newNode;
    }

    // Update the position of a connection when node positions change
    Connection updateConnection(Connection connection)
    {
        // Get objects from the connection structure
        GameObject connectionObj = connection.connectionObject;
        GameObject node1Obj = connection.node1Object;
        GameObject node2Obj = connection.node2Object;

        // Get the size and position of both nodes
        Vector3 node1Size = node1Obj.transform.lossyScale;
        Vector3 node2Size = node2Obj.transform.lossyScale;
        Vector3 node1Position = node1Obj.transform.position;
        Vector3 node2Position = node2Obj.transform.position;

        // Calculate delta vector between the nodes
        Vector3 delta = node2Position - node1Position;

        // Get the radius of both nodes
        float radius1 = node1Size.x / 4f;
        float radius2 = node2Size.x / 4f;

        // Calculate offset from center to the edge for both nodes
        Vector3 offset1 = delta.normalized * radius1;
        Vector3 offset2 = -delta.normalized * radius2;

        // Calculate connection length
        float connectionLength = (float)((delta.magnitude / 2f) - radius1 - radius2);

        // Calculate connection size based on smaller of the two nodes
        float connectionSize = 0;
        if (node1Size.x < node2Size.x)
        {
            connectionSize = (float)(node1Size.x / 10f);
        }
        else
        {
            connectionSize = (float)(node2Size.x / 10f);
        }

        // Transform the connection to be in the correct position
        connectionObj.transform.up = delta;
        connectionObj.transform.position = ((node1Position + node2Position) / 2f) + offset1 + offset2;
        connectionObj.transform.localScale = new Vector3(connectionSize, connectionLength, connectionSize);

        // update connection structure with the modified connection
        connection.connectionObject = connectionObj;

        return connection;
    }

    // Create a connection between two nodes
    Connection createConnection(GameObject node1, GameObject node2)
    {
        System.Random rnd = new System.Random();

        GameObject connectionObject = Instantiate(connectionPrefab, new Vector3(0, 0, 0), Quaternion.identity) as GameObject;

        Connection connection;
        connection.node1Object = node1;
        connection.node2Object = node2;
        connection.connectionObject = connectionObject;
        connection.numPackets = (int)(rnd.NextDouble() * 50);

        // Try heatmap
        // implement function
        //also need to add alpha to colors
        connection.connectionObject.GetComponent<Renderer>().material.color = new Color(233 / 255f, 79 / 255f, 55 / 255f, 150 / 255f);

        // Set position of the connection
        connection = updateConnection(connection);

        return connection;
    }

    // Generate a random node position vector
    Vector3 randomPosVector()
    {
        System.Random rnd = new System.Random();

        float x = (float)((rnd.NextDouble() * 2) - 1); // -1 to 1
        float y = (float)((rnd.NextDouble() * 2) + 0.1); // .1 - 2.1
        float z = (float)((rnd.NextDouble() * 2) - 1); // -1 to 1

        return new Vector3(x, y, z);
    }

    // Generate a random node size vector
    Vector3 randomSizeVector()
    {
        System.Random rnd = new System.Random();
        float a = (float)(rnd.NextDouble() * 0.3);
        return new Vector3(a, a, a);
    }

    // Generate a vector of all zeros
    Vector3 zeroVector()
    {
        return new Vector3(0, 0, 0);
    }

    // Start is called before the first frame update
    void Start()
    {
        // Random number generator
        System.Random rnd = new System.Random();

        // Create 20 nodes
        for (int i = 0; i < 20; i++)
        {
            GameObject node = createNode(randomPosVector(), zeroVector(), randomSizeVector());
            node.transform.SetParent(scaleObject);
            nodeList.Add(node);
        }

        // Connect nodes at random
        for (int i = 0; i < 15; i++)
        {
            var rand1 = rnd.Next(nodeList.Count);
            var rand2 = rnd.Next(nodeList.Count);
            while (rand1 == rand2)
            {
                rand1 = rnd.Next(nodeList.Count);
                rand2 = rnd.Next(nodeList.Count);
            }

            Connection connection;
            connection = createConnection(nodeList[rand1], nodeList[rand2]);
            connectionList.Add(connection);
        }

    }

    // Update is called once per frame
    void Update()
    {
        // Update the position of every connection in the connection list every frame
        for (int i = 0; i < connectionList.Count; i++)
        {
            connectionList[i] = updateConnection(connectionList[i]);
        }
    }
}