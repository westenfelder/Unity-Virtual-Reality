using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;

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

    private static int NUMNODES = 100;
    private static int NUMCONNECTIONS = 50;
    private int[,] connectionArray = new int[NUMNODES, NUMNODES];

    // Create a node given position, rotation, and scale vectors
    GameObject createNode(Vector3 position, Vector3 scale)
    {

        System.Random rnd = new System.Random();

        GameObject newNode = Instantiate(nodePrefab, Vector3.zero, Quaternion.identity) as GameObject;
        newNode.transform.localScale = scale;
        newNode.transform.localPosition = position;

        int r, g, b;
        (r, g, b) = heatMap(0, 20, ((int)(rnd.NextDouble() * 20)));

        newNode.GetComponent<Renderer>().material.color = new Color32((byte)r, (byte)g, (byte)b, 255);

        return newNode;

    }

    // Update the position of a connection when node positions change
    Connection updateConnection(Connection connection)
    {
        // Get objects from the connection structure
        GameObject connectionObj = connection.connectionObject;

        // Get the size and position of both nodes
        Vector3 node1Size = connection.node1Object.transform.lossyScale;
        Vector3 node2Size = connection.node2Object.transform.lossyScale;
        Vector3 node1Position = connection.node1Object.transform.position;
        Vector3 node2Position = connection.node2Object.transform.position;

        // Calculate delta vector between the nodes
        Vector3 delta = node2Position - node1Position;

        // Get the radius of both nodes
        float radius1 = node1Size.x / 4f;
        float radius2 = node2Size.x / 4f;

        // Calculate connection length
        float connectionLength = (float) (delta.magnitude / 2f);

        // Calculate connection size based on smaller of the two nodes
        float connectionSize;
        if (node1Size.x < node2Size.x)
        {
            connectionSize = (float)(node1Size.x / 5f);
        }
        else
        {
            connectionSize = (float)(node2Size.x / 5f);
        }

        // Transform the connection to be in the correct position
        connectionObj.transform.up = delta;
        connectionObj.transform.position = ((node1Position + node2Position) / 2f);
        connectionObj.transform.localScale = new Vector3(connectionSize, connectionLength, connectionSize);

        // update connection structure with the modified connection
        connection.connectionObject = connectionObj;

        return connection;
    }

    (int, int, int) heatMap(int min, int max, int value)
    {
        // Don't want spectrum to wrap fully because that would be confusing for heat map
        double x = (5.25 * value) / (max + min);
        // shift spectrum to start at purple
        x = (x - 0.25) % 6;
        double frac = Math.Abs(x - Math.Floor(x));

        int r = 0;
        int g = 0;
        int b = 0;
        if (0 <= x && x < 1)
        {
            r = 0;
            g = (int)(frac * 255);
            b = 255;
        }
        else if (1 <= x && x < 2)
        {
            r = 0;
            g = 255;
            b = (int)((1 - frac) * 255);
        }
        else if (2 <= x && x < 3)
        {
            r = (int)(frac * 255);
            g = 255;
            b = 0;
        }
        else if (3 <= x && x < 4)
        {
            r = 255;
            g = (int)((1 - frac) * 255);
            b = 0;
        }
        else if (4 <= x && x < 5)
        {
            r = 255;
            g = 0;
            b = (int)(frac * 255);
        }
        else if (5 <= x && x <= 6)
        {
            r = (int)((1 - frac) * 255);
            g = 0;
            b = 255;
        }

        return (r, g, b);

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

        int r, g, b;
        (r, g, b) = heatMap(0, 50, connection.numPackets);

        connection.connectionObject.GetComponent<Renderer>().material.color = new Color32((byte) r, (byte) g, (byte) b, 255);

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
        float a = (float)((rnd.NextDouble() * 0.3) + 0.05); //0.05 - 0.35
        return new Vector3(a, a, a);
    }

    // Start is called before the first frame update
    void Start()
    {
        // Random number generator
        System.Random rnd = new System.Random();

        //disable grabbing components until physics is complete
        nodePrefab.GetComponent<Oculus.Interaction.Grabbable>().enabled = false;
        nodePrefab.GetComponent<Oculus.Interaction.HandGrab.HandGrabInteractable>().enabled = false;

        // Create nodes
        for (int i = 0; i < NUMNODES; i++)
        {
            GameObject node = createNode(randomPosVector(), randomSizeVector());
            node.transform.SetParent(scaleObject);
            nodeList.Add(node);
        }

        // Make connections
        for (int i = 0; i < NUMCONNECTIONS; i++)
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

            //add connection to the connection array
            connectionArray[rand1, rand2] = 1;
            connectionArray[rand2, rand1] = 1;
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

        if (scaleObject.transform.lossyScale == new Vector3(5, 5, 5))
        {

            //Apply gravity forces
            for (int i = 0; i < nodeList.Count; i++)
            {

                nodeList[i].GetComponent<Rigidbody>().isKinematic = true;
                nodeList[i].GetComponent<Rigidbody>().isKinematic = false;

                for (int j = 0; j < nodeList.Count; j++)
                {
                    float node1size = nodeList[i].transform.lossyScale.x;
                    float node2size = nodeList[j].transform.lossyScale.x;

                    if (i != j)
                    {
                        //add force away from other nodes
                        if (connectionArray[i, j] == 0)
                        {
                            Vector3 direction = (nodeList[i].transform.localPosition - nodeList[j].transform.localPosition).normalized;
                            float distance = Vector3.Distance(nodeList[i].transform.localPosition, nodeList[j].transform.localPosition);
                            Vector3 force = (direction * node1size * node2size) / (distance * distance);
                            force = Vector3.ClampMagnitude(force, 1f);
                            nodeList[i].GetComponent<Rigidbody>().AddForce(force);
                        }

                        //twoards connected
                        if (connectionArray[i, j] == 1)
                        {
                            Vector3 direction = (nodeList[i].transform.localPosition - nodeList[j].transform.localPosition).normalized;
                            float desiredDistance = .1f;
                            float distance = Vector3.Distance(nodeList[i].transform.localPosition, nodeList[j].transform.localPosition) - desiredDistance;
                            Vector3 force = direction * node1size * node2size * distance * nodeList.Count * nodeList.Count * nodeList.Count;
                            force = Vector3.ClampMagnitude(force, 10f);
                            nodeList[i].GetComponent<Rigidbody>().AddForce(-force);
                        }
                    }
                }
            }
        }

        else
        {
            for (int i = 0; i < nodeList.Count; i++)
            {
                nodeList[i].GetComponent<Rigidbody>().isKinematic = true;

                nodeList[i].GetComponent<Oculus.Interaction.Grabbable>().enabled = true;
                nodeList[i].GetComponent<Oculus.Interaction.HandGrab.HandGrabInteractable>().enabled = true;
            }

        }




    }
}